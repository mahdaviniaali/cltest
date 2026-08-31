from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.search import Search
from app.repositories.advertisement_repository import AdvertisementRepository
from app.repositories.crawl_job_repository import CrawlJobRepository
from app.repositories.crawler_state_repository import CrawlerStateRepository
from app.services.search_refresh import SearchRefreshService


@dataclass(slots=True)
class FilterCriteria:
    brand: Optional[str] = None
    model: Optional[str] = None
    min_year: Optional[int] = None
    max_price: Optional[int] = None
    max_mileage: Optional[int] = None
    location: Optional[str] = None


@dataclass(slots=True)
class DataPreviewResult:
    ads: list
    total_count: int
    last_updated_at: Optional[datetime]
    is_refreshing: bool
    bootstrapped: bool = False
    cache_sufficient: bool = False
    pages_crawled: int = 0
    ads_found: int = 0
    ads_new: int = 0


class DataPreviewService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._ads = AdvertisementRepository(session)
        self._state = CrawlerStateRepository(session)
        self._jobs = CrawlJobRepository(session)

    def preview(self, criteria: FilterCriteria, *, limit: int = 20) -> DataPreviewResult:
        ads = self._ads.list_matching_filter(
            brand=criteria.brand,
            model=criteria.model,
            min_year=criteria.min_year,
            max_price=criteria.max_price,
            max_mileage=criteria.max_mileage,
            location=criteria.location,
            limit=limit,
        )
        total = len(
            self._ads.list_matching_filter(
                brand=criteria.brand,
                model=criteria.model,
                min_year=criteria.min_year,
                max_price=criteria.max_price,
                max_mileage=criteria.max_mileage,
                location=criteria.location,
                limit=1000,
            )
        )
        last_updated = max((ad.crawled_at for ad in ads), default=None) or self._global_last_updated()
        return DataPreviewResult(
            ads=ads,
            total_count=total,
            last_updated_at=last_updated,
            is_refreshing=self._is_refreshing(),
        )

    def preview_for_search(self, search: Search, *, limit: int = 50) -> DataPreviewResult:
        from crawler.application.on_demand_crawl import OnDemandCrawlService

        criteria = FilterCriteria(
            brand=search.brand,
            model=search.model,
            min_year=search.min_year,
            max_price=search.max_price,
            max_mileage=search.max_mileage,
            location=search.location,
        )
        result = self.preview(criteria, limit=limit)
        cache = OnDemandCrawlService(self._session).evaluate_cache_for_search(search)
        refresh_svc = SearchRefreshService(self._session)
        last_updated = refresh_svc.max_matching_crawled_at(search) or result.last_updated_at
        job = self._jobs.get_active_for_search(search.id)
        return DataPreviewResult(
            ads=result.ads,
            total_count=result.total_count,
            last_updated_at=last_updated,
            is_refreshing=self._is_refreshing_for_search(search.id),
            bootstrapped=search.bootstrapped_at is not None,
            cache_sufficient=cache.sufficient,
            pages_crawled=job.pages_crawled if job else 0,
            ads_found=job.ads_found if job else 0,
            ads_new=job.ads_new if job else 0,
        )

    def status(self) -> tuple[Optional[datetime], bool]:
        return self._global_last_updated(), self._is_refreshing()

    def _global_last_updated(self) -> Optional[datetime]:
        state = self._state.get()
        return state.last_crawl_at if state else None

    def _is_refreshing(self) -> bool:
        return self._jobs.get_any_running() is not None

    def _is_refreshing_for_search(self, search_id: int) -> bool:
        from app.models.search import Search

        self._jobs.reconcile_abandoned_pending_jobs()
        search = self._session.get(Search, search_id)
        if search and search.filter_fingerprint:
            if self._jobs.get_active_for_fingerprint(search.filter_fingerprint) is not None:
                return True
        return self._jobs.get_active_for_search(search_id) is not None
