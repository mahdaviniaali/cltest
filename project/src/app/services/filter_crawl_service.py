from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.crawl_job import CrawlJob, CrawlJobType
from app.models.search import Search
from app.repositories.crawl_job_repository import CrawlJobRepository
from app.repositories.filter_crawl_state_repository import FilterCrawlStateRepository
from config import settings
from crawler.application.filter_listing_url_builder import build_filter_listing_url


@dataclass(slots=True)
class FilterCrawlEnqueueResult:
    used_cache: bool
    job_id: Optional[str] = None
    filter_fingerprint: Optional[str] = None
    is_crawling: bool = False


class FilterCrawlService:
    """Shared per-filter crawl orchestration (dedup + freshness)."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._jobs = CrawlJobRepository(session)
        self._states = FilterCrawlStateRepository(session)

    def prepare_search(self, search: Search) -> str:
        listing = build_filter_listing_url(self._session, search)
        fp = self._states.ensure_fingerprint_on_search(search, listing.url)
        self._session.commit()
        self._session.refresh(search)
        return fp.fingerprint

    def is_filter_fresh(self, fingerprint: str) -> bool:
        state = self._states.get(fingerprint)
        if state is None or state.last_crawl_at is None:
            return False
        ts = state.last_crawl_at
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - ts).total_seconds()
        return age <= settings.CRAWL_STALENESS_SECONDS

    def get_active_job_for_fingerprint(self, fingerprint: str) -> Optional[CrawlJob]:
        return self._jobs.get_active_for_fingerprint(fingerprint)

    def enqueue_for_search(
        self,
        search: Search,
        *,
        triggered_by: str,
        force: bool = False,
    ) -> FilterCrawlEnqueueResult:
        fingerprint = search.filter_fingerprint or self.prepare_search(search)

        if not force and self.is_filter_fresh(fingerprint):
            return FilterCrawlEnqueueResult(
                used_cache=True,
                filter_fingerprint=fingerprint,
            )

        active = self.get_active_job_for_fingerprint(fingerprint)
        if active is not None:
            return FilterCrawlEnqueueResult(
                used_cache=False,
                job_id=active.id,
                filter_fingerprint=fingerprint,
                is_crawling=True,
            )

        job = self._jobs.create(
            job_type=CrawlJobType.ON_DEMAND_FILTER.value,
            triggered_by=triggered_by,
            search_id=search.id,
            filter_fingerprint=fingerprint,
            idempotency_key=f"filter:{fingerprint}:{uuid4()}",
        )
        self._session.commit()
        return FilterCrawlEnqueueResult(
            used_cache=False,
            job_id=job.id,
            filter_fingerprint=fingerprint,
            is_crawling=True,
        )

    def enqueue_stale_active_filters(self, *, limit: int = 20) -> list[str]:
        stale = self._states.list_stale_active(
            max_age_seconds=settings.CRAWL_INTERVAL_SECONDS,
            limit=limit,
        )
        job_ids: list[str] = []
        for state in stale:
            if self.get_active_job_for_fingerprint(state.fingerprint) is not None:
                continue
            search_id = self._session.scalar(
                select(Search.id)
                .where(Search.filter_fingerprint == state.fingerprint, Search.enabled.is_(True))
                .limit(1)
            )
            if search_id is None:
                continue
            job = self._jobs.create(
                job_type=CrawlJobType.ON_DEMAND_FILTER.value,
                triggered_by=f"beat:filter:{state.fingerprint[:8]}",
                search_id=search_id,
                filter_fingerprint=state.fingerprint,
                idempotency_key=f"beat-filter:{state.fingerprint}:{uuid4()}",
            )
            job_ids.append(job.id)
        if job_ids:
            self._session.commit()
        return job_ids

    def list_active_for_admin(self, *, limit: int = 200) -> list[dict]:
        rows = self._states.list_active(limit=limit)
        result: list[dict] = []
        for row in rows:
            active = self.get_active_job_for_fingerprint(row.fingerprint)
            result.append(
                {
                    "fingerprint": row.fingerprint,
                    "section_key": row.section_key,
                    "listing_url": row.listing_url,
                    "brand": row.brand,
                    "model": row.model,
                    "min_year": row.min_year,
                    "max_price": row.max_price,
                    "max_mileage": row.max_mileage,
                    "location": row.location,
                    "last_seen_bama_id": row.last_seen_bama_id,
                    "last_crawl_at": row.last_crawl_at,
                    "last_job_id": row.last_job_id,
                    "enabled_search_count": row.enabled_search_count,
                    "active_job_id": active.id if active else None,
                    "active_job_status": active.status if active else None,
                }
            )
        return result
