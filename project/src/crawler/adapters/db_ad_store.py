from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.db.unit_of_work import UnitOfWork
from app.repositories.advertisement_repository import AdvertisementRepository
from app.repositories.crawler_state_repository import CrawlerStateRepository
from app.repositories.outbox_repository import OutboxRepository
from crawler.domain.entities import AdDraft
from crawler.domain.ports import AdStore, CrawlCheckpointStore


class DbAdStore(AdStore):
    def __init__(self, session: Session) -> None:
        self._session = session
        self._ads = AdvertisementRepository(session)
        self._outbox = OutboxRepository(session)

    def save_new(self, draft: AdDraft) -> tuple[int, bool]:
        data = self._to_row(draft)
        ad, created = self._ads.add_new(data)
        if created:
            self._outbox.enqueue(
                event_type="ad.created",
                aggregate_id=draft.bama_id,
                payload={"bama_id": draft.bama_id, "ad_id": ad.id},
            )
            self._session.commit()
            self._session.refresh(ad)
        return ad.id, created

    def _to_row(self, draft: AdDraft) -> dict[str, Any]:
        return {
            "bama_id": draft.bama_id,
            "url": draft.url,
            "title": draft.title,
            "brand": draft.brand,
            "model": draft.model,
            "year": draft.year,
            "price": draft.price,
            "mileage": draft.mileage,
            "location": draft.location,
            "description": draft.description,
            "published_at": draft.published_at,
            "raw_data": draft.raw_data,
            "crawled_at": datetime.now(timezone.utc),
        }


class DbCrawlCheckpointStore(CrawlCheckpointStore):
    def __init__(self, session: Session, source_key: str = "bama:car:listings") -> None:
        self._session = session
        self._source_key = source_key
        self._repo = CrawlerStateRepository(session)

    def get_last_seen_bama_id(self) -> str | None:
        state = self._repo.get(self._source_key)
        return state.last_seen_bama_id if state else None

    def update_checkpoint(self, bama_id: str, job_id: str) -> None:
        self._repo.update_checkpoint(
            last_seen_bama_id=bama_id,
            job_id=job_id,
            source_key=self._source_key,
        )
        self._session.commit()
