from datetime import datetime, timezone

from app.models.advertisement import Advertisement
from app.repositories.outbox_repository import OutboxRepository
from crawler.adapters.db_ad_store import DbAdStore
from crawler.domain.entities import AdDraft


def test_db_ad_store_writes_outbox_in_same_transaction(db_session):
    store = DbAdStore(db_session)
    ad_id, created = store.save_new(
        AdDraft(
            bama_id="9001",
            url="https://bama.ir/car/detail-9001",
            title="Test Car",
            brand="Renault",
            model="Megane",
        )
    )
    assert created is True
    assert ad_id > 0

    outbox = OutboxRepository(db_session)
    events = outbox.claim_pending()
    assert len(events) == 1
    assert events[0].payload["bama_id"] == "9001"
    assert events[0].payload["ad_id"] == ad_id


def test_db_ad_store_dedup_skips_outbox(db_session):
    db_session.add(
        Advertisement(
            bama_id="9002",
            url="https://bama.ir/car/detail-9002",
            title="Existing",
            crawled_at=datetime.now(timezone.utc),
        )
    )
    db_session.commit()

    store = DbAdStore(db_session)
    _, created = store.save_new(
        AdDraft(
            bama_id="9002",
            url="https://bama.ir/car/detail-9002",
            title="Existing",
        )
    )
    assert created is False

    outbox = OutboxRepository(db_session)
    assert outbox.claim_pending() == []
