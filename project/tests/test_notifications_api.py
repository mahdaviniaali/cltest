from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_current_user, get_db
from app.api.main import app as fastapi_app
from app.db.base import Base
from app.models.advertisement import Advertisement
from app.models.match import Match
from app.models.notification import Notification, NotificationStatus
from app.models.search import Search
from app.models.user import User


@pytest.fixture()
def client():
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
    import app.models.site_map  # noqa: F401
    import app.models.user  # noqa: F401

    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    session = Session()

    user = User(id=1, email="inbox@test.com", password_hash="hash")
    session.add(user)
    session.flush()
    search = Search(user_id=1, name="فیلتر", brand="تویوتا", enabled=True)
    session.add(search)
    session.flush()
    ad = Advertisement(
        bama_id="inbox1",
        url="https://bama.ir/car/detail-inbox1",
        title="Test Ad",
        crawled_at=datetime.now(timezone.utc),
    )
    session.add(ad)
    session.flush()
    match = Match(ad_id=ad.id, search_id=search.id)
    session.add(match)
    session.flush()
    session.add(
        Notification(
            match_id=match.id,
            user_id=1,
            channel="in_app",
            title="Test Ad",
            body="فیلتر: فیلتر",
            status=NotificationStatus.SENT.value,
        )
    )
    session.commit()

    def override_db():
        yield session

    def override_user():
        return user

    fastapi_app.dependency_overrides[get_db] = override_db
    fastapi_app.dependency_overrides[get_current_user] = override_user
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()
    session.close()


def test_list_notifications(client):
    response = client.get("/api/notifications")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Test Ad"


def test_unread_count_and_mark_read(client):
    count = client.get("/api/notifications/unread-count")
    assert count.status_code == 200
    assert count.json()["count"] == 1

    notif_id = client.get("/api/notifications").json()[0]["id"]
    read = client.patch(f"/api/notifications/{notif_id}/read")
    assert read.status_code == 200
    assert read.json()["read_at"] is not None

    count2 = client.get("/api/notifications/unread-count")
    assert count2.json()["count"] == 0


def test_health_ready_ok(client):
    with patch("redis.from_url") as mock_redis:
        mock_redis.return_value.ping.return_value = True
        response = client.get("/api/health/ready")
        assert response.status_code == 200
        assert response.json()["status"] == "ready"
