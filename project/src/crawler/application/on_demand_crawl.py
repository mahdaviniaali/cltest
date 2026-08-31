from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.crawl_job import CrawlJobType
from app.repositories.advertisement_repository import AdvertisementRepository
from app.repositories.crawl_job_repository import CrawlJobRepository
from app.repositories.filter_crawl_state_repository import FilterCrawlStateRepository
from app.repositories.search_repository import SearchRepository
from app.services.filter_crawl_service import FilterCrawlService
from config import settings
from crawler.domain.entities import OnDemandCrawlResult


@dataclass(slots=True)
class CacheEvaluation:
    cached_count: int
    sufficient: bool
    fresh_enough: bool
    filter_fresh: bool = False


class OnDemandCrawlService:
    """Fast path from shared filter cache or enqueue filter incremental crawl."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._ads = AdvertisementRepository(session)
        self._searches = SearchRepository(session)
        self._jobs = CrawlJobRepository(session)
        self._filter_states = FilterCrawlStateRepository(session)
        self._filter_crawl = FilterCrawlService(session)

    def evaluate_search(self, search_id: int, user_id: int) -> OnDemandCrawlResult:
        search = self._searches.get_for_user(user_id, search_id)
        if search is None:
            raise ValueError("Search not found")

        self._filter_crawl.prepare_search(search)
        cache = self.evaluate_cache_for_search(search)
        if cache.sufficient:
            return OnDemandCrawlResult(used_cache=True, job_id=None, cached_count=cache.cached_count)

        enqueue = self._filter_crawl.enqueue_for_search(
            search,
            triggered_by=f"search:{search_id}",
        )
        return OnDemandCrawlResult(
            used_cache=False,
            job_id=enqueue.job_id,
            cached_count=cache.cached_count,
        )

    def evaluate_cache_for_search(self, search: Any) -> CacheEvaluation:
        if search.filter_fingerprint:
            filter_fresh = self._filter_crawl.is_filter_fresh(search.filter_fingerprint)
        else:
            filter_fresh = False

        cached = self._ads.list_matching_filter(
            brand=search.brand,
            model=search.model,
            min_year=search.min_year,
            max_price=search.max_price,
            max_mileage=search.max_mileage,
            location=search.location,
            limit=settings.CRAWL_ON_DEMAND_CACHE_MIN_COUNT + 1,
        )
        cached_count = len(cached)
        fresh_enough = filter_fresh or self._is_cache_fresh(cached)
        sufficient = fresh_enough and (filter_fresh or cached_count >= 1)
        return CacheEvaluation(
            cached_count=cached_count,
            sufficient=sufficient,
            fresh_enough=fresh_enough,
            filter_fresh=filter_fresh,
        )

    def trigger_global(self) -> str:
        job = self._jobs.create(
            job_type=CrawlJobType.ON_DEMAND_GLOBAL.value,
            triggered_by="api",
            idempotency_key=f"on-demand-global:{uuid4()}",
        )
        self._session.commit()
        return job.id

    def _is_cache_fresh(self, ads: list[Any]) -> bool:
        if not ads:
            return False
        newest = max(ad.crawled_at for ad in ads)
        if newest.tzinfo is None:
            newest = newest.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - newest).total_seconds()
        return age <= settings.CRAWL_STALENESS_SECONDS

    def filter_last_updated(self, search: Any) -> Optional[datetime]:
        if not search.filter_fingerprint:
            return None
        state = self._filter_states.get(search.filter_fingerprint)
        return state.last_crawl_at if state else None
