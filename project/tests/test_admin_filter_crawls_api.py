from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_current_user, get_db
from app.api.main import app
from app.db.base import Base
from app.models.filter_crawl_state import FilterCrawlState
from app.models.search import Search
from app.models.user import User
from app.services.filter_crawl_service import FilterCrawlService


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    import app.models.filter_crawl_state  # noqa: F401
    import app.models.search  # noqa: F401
    import app.models.user  # noqa: F401

    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    user = User(id=1, email="admin@example.com", password_hash="hash")
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


def test_admin_filter_crawls_lists_active(client, db_session):
    search = Search(user_id=1, brand="BMW", model="X5", enabled=True)
    db_session.add(search)
    db_session.commit()
    db_session.refresh(search)

    FilterCrawlService(db_session).prepare_search(search)
    state = db_session.get(FilterCrawlState, search.filter_fingerprint)
    state.last_crawl_at = datetime.now(timezone.utc)
    state.enabled_search_count = 1
    db_session.commit()

    response = client.get("/api/admin/filter-crawls")
    assert response.status_code == 200
    body = response.json()
    assert len(body) >= 1
    row = next(item for item in body if item["fingerprint"] == search.filter_fingerprint)
    assert row["brand"] == "BMW"
    assert row["enabled_search_count"] == 1
    assert row["last_crawl_at"] is not None
