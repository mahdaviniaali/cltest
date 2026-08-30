from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.crawl_job import CrawlJobType
from app.models.search import Search
from app.repositories.advertisement_repository import AdvertisementRepository
from app.repositories.crawl_job_repository import CrawlJobRepository
from app.repositories.search_repository import SearchRepository
from config import settings
from crawler.application.on_demand_crawl import OnDemandCrawlService


@dataclass(slots=True)
class SearchRefreshResult:
    is_refreshing: bool
    message: str
    job_id: Optional[str] = None
    used_bootstrap: bool = False


class SearchRefreshService:
    """Search-scoped refresh with handoff to global incremental after bootstrap."""

    REFRESH_MESSAGE = "داده‌ها در حال بروزرسانی هستند"

    def __init__(self, session: Session) -> None:
        self._session = session
        self._searches = SearchRepository(session)
        self._jobs = CrawlJobRepository(session)
        self._ads = AdvertisementRepository(session)
        self._on_demand = OnDemandCrawlService(session)

    def request_refresh(
        self,
        search: Search,
        *,
        force: bool = False,
    ) -> SearchRefreshResult:
        if self._jobs.get_running_for_search(search.id) is not None:
            return SearchRefreshResult(is_refreshing=True, message=self.REFRESH_MESSAGE)

        if self._jobs.get_any_running() is not None:
            return SearchRefreshResult(is_refreshing=True, message=self.REFRESH_MESSAGE)

        cache = self._on_demand.evaluate_cache_for_search(search)

        if cache.sufficient and search.bootstrapped_at is not None:
            job = self._jobs.create(
                job_type=CrawlJobType.ON_DEMAND_GLOBAL.value,
                triggered_by=f"search_handoff:{search.id}",
                idempotency_key=f"search-handoff:{search.id}:{uuid4()}",
            )
            self._session.commit()
            return SearchRefreshResult(
                is_refreshing=True,
                message=self.REFRESH_MESSAGE,
                job_id=job.id,
                used_bootstrap=False,
            )

        job = self._jobs.create(
            job_type=CrawlJobType.ON_DEMAND_SEARCH.value,
            triggered_by=f"search_refresh:{search.id}",
            search_id=search.id,
            idempotency_key=f"search-refresh:{search.id}:{uuid4()}",
        )
        self._session.commit()
        return SearchRefreshResult(
            is_refreshing=True,
            message=self.REFRESH_MESSAGE,
            job_id=job.id,
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
