"""Tests for ADR-011 task/job/filter model."""

from datetime import datetime, timedelta, timezone
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
from app.models.filter_crawl_state import FilterCrawlState
from app.models.search import Search
from app.models.user import User
from app.repositories.search_repository import SearchRepository
from app.services.filter_crawl_service import FilterCrawlService
from app.services.matching import MatchingService


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
    import app.models.filter_crawl_state  # noqa: F401
    import app.models.match  # noqa: F401
    import app.models.outbox_event  # noqa: F401
    import app.models.search  # noqa: F401
    import app.models.user  # noqa: F401

    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
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


def _prepare_fingerprint_state(
    db_session,
    search: Search,
    *,
    last_crawl_at: datetime | None = None,
) -> FilterCrawlState:
    service = FilterCrawlService(db_session)
    service.prepare_search(search)
    db_session.commit()
    db_session.refresh(search)
    state = db_session.get(FilterCrawlState, search.filter_fingerprint)
    assert state is not None
    state.last_crawl_at = last_crawl_at
    db_session.commit()
    return state


def test_beat_priority_by_user_count(db_session):
    old = datetime.now(timezone.utc) - timedelta(hours=2)
    s_low = Search(user_id=1, brand="Toyota", model="Corolla", enabled=True)
    s_high = Search(user_id=1, brand="Benz", model="E200", enabled=True)
    db_session.add_all([s_low, s_high])
    db_session.commit()

    _prepare_fingerprint_state(db_session, s_low, last_crawl_at=old)
    high_fp = _prepare_fingerprint_state(db_session, s_high, last_crawl_at=old).fingerprint

    for i in range(4):
        extra = Search(user_id=1, brand="Benz", model="E200", enabled=True)
        db_session.add(extra)
        db_session.commit()
        FilterCrawlService(db_session).prepare_search(extra)
        assert extra.filter_fingerprint == high_fp

    from app.repositories.filter_crawl_state_repository import FilterCrawlStateRepository

    stale = FilterCrawlStateRepository(db_session).list_stale_active(
        max_age_seconds=300,
        limit=10,
    )
    assert len(stale) == 2
    assert stale[0].fingerprint == high_fp
    assert stale[0].enabled_search_count == 5
    assert stale[1].fingerprint == s_low.filter_fingerprint


def test_find_users_by_fingerprint(db_session):
    s1 = Search(user_id=1, brand="Porsche", model="Panamera", enabled=True)
    s2 = Search(user_id=1, brand="Porsche", model="Panamera", enabled=True)
    s3 = Search(user_id=1, brand="Porsche", model="Panamera", enabled=False)
    db_session.add_all([s1, s2, s3])
    db_session.commit()

    FilterCrawlService(db_session).prepare_search(s1)
    fp = s1.filter_fingerprint
    s2.filter_fingerprint = fp
    s3.filter_fingerprint = fp
    db_session.commit()

    repo = SearchRepository(db_session)
    users = repo.list_enabled_by_fingerprint(fp)
    assert len(users) == 2
    assert {u.id for u in users} == {s1.id, s2.id}

    by_brand = repo.list_enabled_by_brand("Porsche")
    assert len(by_brand) == 2


def test_match_sql_prefilter(db_session):
    user = User(email="match@test.com", password_hash="hash")
    db_session.add(user)
    db_session.flush()

    renault = Search(user_id=user.id, brand="Renault", enabled=True)
    toyota = Search(user_id=user.id, brand="Toyota", enabled=True)
    expensive = Search(user_id=user.id, brand="Renault", max_price=500_000_000, enabled=True)
    db_session.add_all([renault, toyota, expensive])
    db_session.flush()

    ad = Advertisement(
        bama_id="prefilter-1",
        url="https://bama.ir/car/detail-p1",
        title="Renault Megane",
        brand="Renault",
        model="Megane",
        year=1390,
        price=1_000_000_000,
        crawled_at=datetime.now(timezone.utc),
    )
    db_session.add(ad)
    db_session.commit()

    matches = MatchingService(db_session).process_new_ad(ad.id)
    db_session.commit()

    matched_ids = {m.search_id for m in matches}
    assert renault.id in matched_ids
    assert toyota.id not in matched_ids
    assert expensive.id not in matched_ids


@patch("app.api.routes.searches.dispatch_on_demand_job")
def test_search_update_triggers_crawl(mock_dispatch, client, db_session):
    search = Search(user_id=1, brand="Dena", model="Plus", enabled=True)
    db_session.add(search)
    db_session.commit()
    db_session.refresh(search)

    response = client.put(
        f"/api/searches/{search.id}",
        json={"brand": "Toyota", "model": "Corolla"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["brand"] == "Toyota"
    assert body["filter_fingerprint"] is not None
    assert body["is_crawling"] is True
    assert body["job_id"] is not None
    mock_dispatch.assert_called_once_with(body["job_id"])

    db_session.refresh(search)
    assert search.filter_fingerprint == body["filter_fingerprint"]
