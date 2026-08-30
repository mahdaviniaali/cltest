from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.site_map import CrawlEvent


class CrawlEventRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def emit(self, *, job_id: str, event_type: str, payload: Optional[dict[str, Any]] = None) -> CrawlEvent:
        event = CrawlEvent(job_id=job_id, event_type=event_type, payload=payload or {})
        self._session.add(event)
        self._session.flush()
        return event

    def list_since(
        self,
        job_id: str,
        *,
        since_id: int = 0,
        limit: int = 200,
    ) -> list[CrawlEvent]:
        stmt = (
            select(CrawlEvent)
            .where(CrawlEvent.job_id == job_id, CrawlEvent.id > since_id)
            .order_by(CrawlEvent.id)
            .limit(limit)
        )
        return list(self._session.scalars(stmt).all())

    def list_recent(self, job_id: str, *, limit: int = 100) -> list[CrawlEvent]:
        stmt = (
            select(CrawlEvent)
            .where(CrawlEvent.job_id == job_id)
            .order_by(CrawlEvent.id.desc())
            .limit(limit)
        )
        return list(reversed(list(self._session.scalars(stmt).all())))
