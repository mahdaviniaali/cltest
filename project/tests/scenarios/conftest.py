from __future__ import annotations

import sys
from pathlib import Path

# Allow `from helpers...` within tests/scenarios/
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_current_user, get_db
from app.api.main import app
from app.db.base import Base
from app.models.user import User
from helpers.scenario_factory import UserFactory


def _import_models() -> None:
    import app.models.advertisement  # noqa: F401
    import app.models.crawl_job  # noqa: F401
    import app.models.crawler_state  # noqa: F401
    import app.models.filter_crawl_state  # noqa: F401
    import app.models.match  # noqa: F401
    import app.models.notification  # noqa: F401
    import app.models.outbox_event  # noqa: F401
    import app.models.search  # noqa: F401
    import app.models.user  # noqa: F401


@pytest.fixture()
def scenario_db() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    _import_models()
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def ali(scenario_db: Session) -> User:
    return UserFactory.create(scenario_db, email="ali@example.com", full_name="علی")


@pytest.fixture()
def sara(scenario_db: Session) -> User:
    return UserFactory.create(scenario_db, email="sara@example.com", full_name="سارا")


def _client_for_user(session: Session, user: User) -> TestClient:
    def override_db():
        yield session

    def override_user():
        return user

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_user
    return TestClient(app)


@pytest.fixture()
def ali_client(scenario_db: Session, ali: User):
    client = _client_for_user(scenario_db, ali)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture()
def sara_client(scenario_db: Session, sara: User):
    client = _client_for_user(scenario_db, sara)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture()
def bare_client(scenario_db: Session):
    def override_db():
        yield scenario_db

    app.dependency_overrides[get_db] = override_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
