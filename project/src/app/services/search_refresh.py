from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.search import Search
from app.repositories.advertisement_repository import AdvertisementRepository
from app.repositories.crawl_job_repository import CrawlJobRepository
from app.repositories.filter_crawl_state_repository import FilterCrawlStateRepository
from app.services.filter_crawl_service import FilterCrawlService
from config import settings
from crawler.application.on_demand_crawl import OnDemandCrawlService


@dataclass(slots=True)
class SearchRefreshResult:
    is_refreshing: bool
    message: str
    job_id: Optional[str] = None
    used_bootstrap: bool = False


class SearchRefreshService:
    """Search-scoped refresh via shared filter incremental crawl."""

    REFRESH_MESSAGE = "داده‌ها در حال بروزرسانی هستند"

    def __init__(self, session: Session) -> None:
        self._session = session
        self._jobs = CrawlJobRepository(session)
        self._ads = AdvertisementRepository(session)
        self._filter_states = FilterCrawlStateRepository(session)
        self._on_demand = OnDemandCrawlService(session)
        self._filter_crawl = FilterCrawlService(session)

    def request_refresh(
        self,
        search: Search,
        *,
        force: bool = False,
    ) -> SearchRefreshResult:
        from app.services.job_dispatch import _dispatch_on_demand_thread

        stuck = self._jobs.redispatch_stuck_pending(max_age_seconds=15)
        for job_id in stuck:
            _dispatch_on_demand_thread(job_id)

        if search.filter_fingerprint:
            active = self._jobs.get_active_for_fingerprint(search.filter_fingerprint)
            if active is not None:
                return SearchRefreshResult(is_refreshing=True, message=self.REFRESH_MESSAGE, job_id=active.id)

        if self._jobs.get_active_for_search(search.id) is not None:
            return SearchRefreshResult(is_refreshing=True, message=self.REFRESH_MESSAGE)

        self._jobs.reconcile_abandoned_pending_jobs()
        cache = self._on_demand.evaluate_cache_for_search(search)

        if not force and cache.sufficient:
            return SearchRefreshResult(is_refreshing=False, message="cache is fresh")

        enqueue = self._filter_crawl.enqueue_for_search(
            search,
            triggered_by=f"search_refresh:{search.id}",
            force=force,
        )
        return SearchRefreshResult(
            is_refreshing=enqueue.is_crawling,
            message=self.REFRESH_MESSAGE,
            job_id=enqueue.job_id,
            used_bootstrap=True,
        )

    def count_matching(self, search: Search) -> int:
        return len(
            self._ads.list_matching_filter(
                brand=search.brand,
                model=search.model,
                min_year=search.min_year,
                max_price=search.max_price,
                max_mileage=search.max_mileage,
                location=search.location,
                limit=settings.CRAWL_ON_DEMAND_CACHE_MIN_COUNT + 1,
            )
        )

    def max_matching_crawled_at(self, search: Search) -> Optional[datetime]:
        if search.filter_fingerprint:
            state = self._filter_states.get(search.filter_fingerprint)
            if state and state.last_crawl_at:
                return state.last_crawl_at
        ads = self._ads.list_matching_filter(
            brand=search.brand,
            model=search.model,
            min_year=search.min_year,
            max_price=search.max_price,
            max_mileage=search.max_mileage,
            location=search.location,
            limit=settings.CRAWL_ON_DEMAND_CACHE_MIN_COUNT + 1,
        )
        if not ads:
            return None
        return max(ad.crawled_at for ad in ads)
