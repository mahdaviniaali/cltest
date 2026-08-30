from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.advertisement import Advertisement
from app.repositories.advertisement_repository import AdvertisementRepository
from app.repositories.crawl_job_repository import CrawlJobRepository
from app.repositories.crawler_state_repository import CrawlerStateRepository


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
    ads: list[Advertisement]
    total_count: int
    last_updated_at: Optional[datetime]
    is_refreshing: bool


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
        return DataPreviewResult(
            ads=ads,
            total_count=total,
            last_updated_at=self._global_last_updated(),
            is_refreshing=self._is_refreshing(),
        )

    def status(self) -> tuple[Optional[datetime], bool]:
        return self._global_last_updated(), self._is_refreshing()

    def _global_last_updated(self) -> Optional[datetime]:
        state = self._state.get()
        return state.last_crawl_at if state else None

    def _is_refreshing(self) -> bool:
        return self._jobs.get_any_running() is not None
