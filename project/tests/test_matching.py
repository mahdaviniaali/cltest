from datetime import datetime, timezone

from app.models.advertisement import Advertisement
from app.models.search import Search
from app.models.user import User
from app.services.matching import MatchingService


def test_matching_creates_match_and_notify_outbox(db_session):
    user = User(email="a@test.com", password_hash="hash", full_name="A")
    db_session.add(user)
    db_session.flush()

    search = Search(user_id=user.id, brand="Renault", enabled=True)
    db_session.add(search)
    db_session.flush()

    ad = Advertisement(
        bama_id="8001",
        url="https://bama.ir/car/detail-8001",
        title="Renault Megane",
        brand="Renault",
        model="Megane",
        year=1390,
        price=1_000_000_000,
        crawled_at=datetime.now(timezone.utc),
    )
    db_session.add(ad)
    db_session.commit()

    service = MatchingService(db_session)
    matches = service.process_new_ad(ad.id)
    db_session.commit()

    assert len(matches) == 1
    from app.models.outbox_event import OutboxEvent
    from sqlalchemy import select

    notify_events = list(
        db_session.scalars(select(OutboxEvent).where(OutboxEvent.event_type == "notify.requested"))
    )
    assert len(notify_events) == 1
