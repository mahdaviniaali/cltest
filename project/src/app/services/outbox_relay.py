from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.repositories.outbox_repository import OutboxRepository
from app.workers.tasks.match import process_ad
from app.workers.tasks.notify import send_notification

logger = logging.getLogger(__name__)


class OutboxRelayService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._outbox = OutboxRepository(session)

    def relay(self, batch_size: int = 50) -> int:
        events = self._outbox.claim_pending(limit=batch_size)
        processed = 0
        for event in events:
            try:
                if event.event_type == "ad.created":
                    ad_id = event.payload.get("ad_id")
                    if ad_id is None:
                        raise ValueError("ad.created missing ad_id")
                    process_ad.delay(ad_id)
                elif event.event_type == "notify.requested":
                    match_id = event.payload.get("match_id")
                    if match_id is None:
                        raise ValueError("notify.requested missing match_id")
                    send_notification.delay(match_id)
                else:
                    raise ValueError(f"Unknown event type: {event.event_type}")
                self._outbox.mark_done(event)
                processed += 1
            except Exception as exc:
                logger.exception("Outbox relay failed for event %s", event.id)
                if event.attempts >= 5:
                    self._outbox.mark_failed(event, str(exc))
                else:
                    self._outbox.requeue_failed(event)
        return processed
