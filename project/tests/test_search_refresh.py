from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_current_user, get_db
from app.api.main import app
from app.db.base import Base
from app.models.advertisement import Advertisement
from app.models.crawl_job import CrawlJobType
from app.models.search import Search
from app.models.user import User


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    import app.models.advertisement  # noqa: F401
    import app.models.crawl_job  # noqa: F401
    import app.models.filter_crawl_state  # noqa: F401
    import app.models.search  # noqa: F401
    import app.models.user  # noqa: F401

    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    user = User(id=1, email="test@example.com", password_hash="hash")
    session.add(user)
    session.commit()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    def override_db():
        yield db_session

    def override_user():
        return db_session.get(User, 1)

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_user
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@patch("app.api.routes.searches.dispatch_on_demand_job")
def test_search_refresh_returns_fresh_cache(mock_dispatch, client, db_session):
    search = Search(
        user_id=1,
        brand="Dena",
        model="Plus",
        enabled=True,
        bootstrapped_at=datetime.now(timezone.utc),
    )
    db_session.add(search)
    now = datetime.now(timezone.utc)
    for i in range(5):
        db_session.add(
            Advertisement(
                bama_id=f"handoff-{i}",
                url=f"https://bama.ir/car/detail-h{i}",
                title=f"Dena {i}",
                brand="Dena",
                model="Plus",
                crawled_at=now,
            )
        )
    db_session.commit()
    db_session.refresh(search)

    response = client.post(f"/api/searches/{search.id}/refresh")
    assert response.status_code == 202
    body = response.json()
    assert body["is_refreshing"] is False
    assert "cache is fresh" in body["message"]
    mock_dispatch.assert_not_called()


@patch("app.api.routes.searches.dispatch_on_demand_job")
def test_search_refresh_enqueues_filter_job_when_stale(mock_dispatch, client, db_session):
    from app.models.filter_crawl_state import FilterCrawlState
    from app.services.filter_crawl_service import FilterCrawlService

    search = Search(
        user_id=1,
        brand="Dena",
        model="Plus",
        enabled=True,
    )
    db_session.add(search)
    db_session.commit()
    db_session.refresh(search)
    FilterCrawlService(db_session).prepare_search(search)
    state = db_session.get(FilterCrawlState, search.filter_fingerprint)
    state.last_crawl_at = datetime(2020, 1, 1, tzinfo=timezone.utc)
    db_session.commit()
    db_session.refresh(search)

    response = client.post(f"/api/searches/{search.id}/refresh?force=true")
    assert response.status_code == 202
    body = response.json()
    assert body["used_bootstrap"] is True
    assert body["job_id"] is not None
    mock_dispatch.assert_called_once()

    from app.repositories.crawl_job_repository import CrawlJobRepository

    job = CrawlJobRepository(db_session).get(body["job_id"])
    assert job.job_type == CrawlJobType.ON_DEMAND_FILTER.value
