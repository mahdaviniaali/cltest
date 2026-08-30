from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.outbox_event import OutboxEvent, OutboxStatus


class OutboxRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def enqueue(
        self,
        *,
        event_type: str,
        aggregate_id: str,
        payload: dict[str, Any],
    ) -> OutboxEvent:
        event = OutboxEvent(
            event_type=event_type,
            aggregate_id=aggregate_id,
            payload=payload,
            status=OutboxStatus.PENDING.value,
        )
        self._session.add(event)
        self._session.flush()
        return event

    def claim_pending(self, limit: int = 50) -> list[OutboxEvent]:
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.status == OutboxStatus.PENDING.value)
            .order_by(OutboxEvent.id.asc())
            .limit(limit)
        )
        events = list(self._session.scalars(stmt))
        now = datetime.now(timezone.utc)
        for event in events:
            event.status = OutboxStatus.PROCESSING.value
            event.attempts += 1
            event.processed_at = now
        if events:
            self._session.flush()
        return events

    def mark_done(self, event: OutboxEvent) -> None:
        event.status = OutboxStatus.DONE.value
        event.processed_at = datetime.now(timezone.utc)
        event.last_error = None
        self._session.flush()

    def mark_failed(self, event: OutboxEvent, error: str) -> None:
        event.status = OutboxStatus.FAILED.value
        event.last_error = error
        event.processed_at = datetime.now(timezone.utc)
        self._session.flush()

    def requeue_failed(self, event: OutboxEvent) -> None:
        event.status = OutboxStatus.PENDING.value
        self._session.flush()
