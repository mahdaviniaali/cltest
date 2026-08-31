from datetime import datetime, timezone

from app.models.advertisement import Advertisement
from app.models.match import Match
from app.models.notification import Notification
from app.models.search import Search
from app.models.user import User
from app.repositories.notification_repository import NotificationRepository
from app.services.notification_orchestrator import NotificationOrchestrator


def _seed_match(db_session):
    user = User(
        email="notify@test.com",
        password_hash="hash",
        notification_channels=["in_app", "log"],
    )
    db_session.add(user)
    db_session.flush()
    search = Search(
        user_id=user.id,
        name="تویوتا",
        brand="تویوتا",
        enabled=True,
    )
    db_session.add(search)
    db_session.flush()
    ad = Advertisement(
        bama_id="n1",
        url="https://bama.ir/car/detail-n1",
        title="Toyota Corolla",
        brand="تویوتا",
        model="Corolla",
        price=2_800_000_000,
        mileage=80000,
        crawled_at=datetime.now(timezone.utc),
    )
    db_session.add(ad)
    db_session.flush()
    match = Match(ad_id=ad.id, search_id=search.id)
    db_session.add(match)
    db_session.commit()
    return match.id, user.id


def test_orchestrator_creates_in_app_delivery(db_session):
    match_id, user_id = _seed_match(db_session)
    result = NotificationOrchestrator(db_session).orchestrate(match_id)
    db_session.commit()

    assert result["sent"] >= 1
    rows = NotificationRepository(db_session).list_for_user(user_id)
    in_app = next(r for r in rows if r.channel == "in_app")
    assert in_app.title == "Toyota Corolla"
    assert in_app.status == "sent"
    assert in_app.payload is not None
    assert in_app.payload.get("ad_url") == "https://bama.ir/car/detail-n1"


def test_orchestrator_idempotent_per_channel(db_session):
    match_id, _user_id = _seed_match(db_session)
    NotificationOrchestrator(db_session).orchestrate(match_id)
    db_session.commit()
    NotificationOrchestrator(db_session).orchestrate(match_id)
    db_session.commit()

    rows = db_session.query(Notification).filter(Notification.match_id == match_id).all()
    channels = {r.channel for r in rows}
    assert "in_app" in channels
    assert len(rows) == len(channels)
