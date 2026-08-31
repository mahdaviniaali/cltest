from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user, get_db
from app.api.main import app
from app.domain.search_filter import (
    ad_matches_search_criteria,
    brand_matches_filter,
    model_matches_filter,
)
from app.models.advertisement import Advertisement
from app.models.user import User
from app.repositories.advertisement_repository import AdvertisementRepository


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


@pytest.fixture()
def db_session():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from app.db.base import Base
    import app.models.advertisement  # noqa: F401
    import app.models.crawl_job  # noqa: F401
    import app.models.crawler_state  # noqa: F401
    import app.models.match  # noqa: F401
    import app.models.notification  # noqa: F401
    import app.models.outbox_event  # noqa: F401
    import app.models.search  # noqa: F401
    import app.models.user  # noqa: F401

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
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


def test_brand_matches_partial_porsche():
    assert brand_matches_filter("پورش", "پورشه") is True
    assert brand_matches_filter("پورشه", "پورش") is True


def test_model_matches_multi_word_against_short_model():
    assert model_matches_filter("پورشه پانامرا", "پانامرا", ad_title="پورشه پانامرا") is True
    assert model_matches_filter("پانامرا", "پانامرا") is True


def test_ad_matches_search_criteria_porsche():
    ad = SimpleNamespace(
        brand="پورشه",
        model="پانامرا",
        title="پورشه پانامرا",
        year=1400,
        price=5_000_000_000,
        mileage=10_000,
        location="تهران",
    )
    assert ad_matches_search_criteria(ad, brand="پورش", model="پورشه پانامرا") is True


def test_list_matching_filter_partial_brand(db_session):
    db_session.add(
        Advertisement(
            bama_id="porsche-1",
            url="https://bama.ir/car/detail-porsche-1",
            title="پورشه پانامرا",
            brand="پورشه",
            model="پانامرا",
            crawled_at=datetime.now(timezone.utc),
        )
    )
    db_session.commit()

    repo = AdvertisementRepository(db_session)
    matches = repo.list_matching_filter(brand="پورش", model="پانامرا", limit=10)
    assert len(matches) == 1


def test_update_search_clears_brand(client, db_session):
    from app.models.search import Search

    search = Search(user_id=1, brand="Toyota", model="Camry", enabled=True)
    db_session.add(search)
    db_session.commit()
    db_session.refresh(search)

    response = client.put(f"/api/searches/{search.id}", json={"brand": None, "model": None})
    assert response.status_code == 200
    body = response.json()
    assert body["brand"] is None
    assert body["model"] is None
