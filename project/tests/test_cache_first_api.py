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
from app.models.crawl_job import CrawlJob, CrawlJobStatus, CrawlJobType
from app.models.crawler_state import CrawlerState
from app.models.user import User
from app.services.data_preview import DataPreviewService, FilterCriteria


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    import app.models.advertisement  # noqa: F401
    import app.models.crawl_job  # noqa: F401
    import app.models.crawler_state  # noqa: F401
    import app.models.match  # noqa: F401
    import app.models.notification  # noqa: F401
    import app.models.outbox_event  # noqa: F401
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


def test_preview_returns_ads_and_last_updated(db_session):
    db_session.add(
        CrawlerState(
            source_key="bama:car:listings",
            last_seen_bama_id="100",
            last_crawl_at=datetime(2026, 8, 30, 12, 0, tzinfo=timezone.utc),
        )
    )
    db_session.add(
        Advertisement(
            bama_id="200",
            url="https://bama.ir/car/detail-200",
            title="Renault Megane",
            brand="Renault",
            model="Megane",
            crawled_at=datetime.now(timezone.utc),
        )
    )
    db_session.commit()

    result = DataPreviewService(db_session).preview(FilterCriteria(brand="Renault"))
    assert result.total_count == 1
    assert result.last_updated_at is not None
    assert result.is_refreshing is False


def test_preview_shows_refreshing_when_job_running(db_session):
    db_session.add(
        CrawlJob(
            id="job-1",
            job_type=CrawlJobType.SCHEDULED_INCREMENTAL.value,
            status=CrawlJobStatus.RUNNING.value,
            triggered_by="beat",
            idempotency_key="scheduled:1",
            started_at=datetime.now(timezone.utc),
        )
    )
    db_session.commit()

    _, is_refreshing = DataPreviewService(db_session).status()
    assert is_refreshing is True


def test_api_preview_endpoint(client, db_session):
    db_session.add(
        Advertisement(
            bama_id="300",
            url="https://bama.ir/car/detail-300",
            title="Toyota Camry",
            brand="Toyota",
            crawled_at=datetime.now(timezone.utc),
        )
    )
    db_session.commit()

    response = client.post("/api/ads/preview", json={"brand": "Toyota"})
    assert response.status_code == 200
    body = response.json()
    assert body["total_count"] == 1
    assert len(body["ads"]) == 1


@patch("app.api.routes.crawl.on_demand_crawl.delay")
def test_refresh_starts_job_when_idle(mock_delay, client, db_session):
    response = client.post("/api/crawl/refresh")
    assert response.status_code == 202
    body = response.json()
    assert body["is_refreshing"] is True
    assert "بروزرسانی" in body["message"]
    assert "job_id" not in body
    mock_delay.assert_called_once()


@patch("app.api.routes.crawl.on_demand_crawl.delay")
def test_refresh_idempotent_while_running(mock_delay, client, db_session):
    db_session.add(
        CrawlJob(
            id="running-1",
            job_type=CrawlJobType.ON_DEMAND_GLOBAL.value,
            status=CrawlJobStatus.RUNNING.value,
            triggered_by="beat",
            idempotency_key="scheduled:running",
            started_at=datetime.now(timezone.utc),
        )
    )
    db_session.commit()

    response = client.post("/api/crawl/refresh")
    assert response.status_code == 202
    body = response.json()
    assert body["is_refreshing"] is True
    mock_delay.assert_not_called()


@patch("app.workers.tasks.crawl.on_demand_crawl.delay")
def test_create_search_does_not_auto_crawl(mock_delay, client, db_session):
    response = client.post(
        "/api/searches",
        json={"brand": "Renault", "enabled": True},
    )
    assert response.status_code == 201
    mock_delay.assert_not_called()


def test_search_results_endpoint(client, db_session):
    from app.models.search import Search

    search = Search(user_id=1, brand="Honda", enabled=True)
    db_session.add(search)
    db_session.add(
        Advertisement(
            bama_id="400",
            url="https://bama.ir/car/detail-400",
            title="Honda Civic",
            brand="Honda",
            crawled_at=datetime.now(timezone.utc),
        )
    )
    db_session.commit()
    db_session.refresh(search)

    response = client.get(f"/api/searches/{search.id}/results")
    assert response.status_code == 200
    assert response.json()["total_count"] == 1
