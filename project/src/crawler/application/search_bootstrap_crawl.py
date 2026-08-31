from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from app.models.search import Search
from app.repositories.advertisement_repository import AdvertisementRepository
from app.services.city_taxonomy_sync import CityTaxonomySync
from app.repositories.search_repository import SearchRepository
from config import settings
from crawler.adapters.bama.parsers import BamaDetailParser, BamaListingParser
from crawler.adapters.db_ad_store import DbAdStore
from crawler.application.search_listing_url_builder import build_search_listing_url
from crawler.domain.entities import AdDraft, ListingCard
from crawler.domain.ports import DetailParser, ListingParser, PageFetcher

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class SearchBootstrapResult:
    pages_crawled: int
    ads_found: int
    ads_new: int
    matching_count: int
    target_reached: bool


class SearchBootstrapCrawlService:
    """Backfill ads for a search filter by crawling scoped listing pages."""

    def __init__(
        self,
        session: Session,
        fetcher: PageFetcher,
        *,
        search_id: int,
        job_id: str,
        listing_parser: Optional[ListingParser] = None,
        detail_parser: Optional[DetailParser] = None,
        max_pages: Optional[int] = None,
        target_count: Optional[int] = None,
    ) -> None:
        self._session = session
        self._fetcher = fetcher
        self._search_id = search_id
        self._job_id = job_id
        self._searches = SearchRepository(session)
        self._ads = AdvertisementRepository(session)
        self._ad_store = DbAdStore(session)
        self._max_pages = max_pages or settings.CRAWL_BOOTSTRAP_MAX_PAGES
        self._target_count = target_count or settings.CRAWL_ON_DEMAND_CACHE_MIN_COUNT

    def run(self) -> SearchBootstrapResult:
        search = self._session.get(Search, self._search_id)
        if search is None:
            raise ValueError(f"Search not found: {self._search_id}")

        listing_url = build_search_listing_url(self._session, search)
        listing_parser = BamaListingParser(listing_url)
        detail_parser = BamaDetailParser()

        pages_crawled = 0
        ads_found = 0
        ads_new = 0
        seen_ids: set[str] = set()
        target_reached = False

        for page in range(1, self._max_pages + 1):
            url = listing_parser.next_page_url(listing_url, page)
            html = self._fetcher.fetch(url)
            if not html:
                logger.warning("Empty bootstrap listing page: %s", url)
                break

            pages_crawled += 1
            cards = listing_parser.parse(html, page=page)
            if not cards:
                break

            for card in cards:
                if card.bama_id in seen_ids:
                    continue
                seen_ids.add(card.bama_id)
                ads_found += 1
                draft = self._fetch_detail(card, detail_parser)
                if draft is None:
                    continue
                _, created = self._ad_store.save_new(draft)
                if created:
                    ads_new += 1

            matching_count = self._count_matching(search)
            if matching_count >= self._target_count or ads_new >= self._target_count:
                target_reached = True
                break

        matching_count = self._count_matching(search)
        target_reached = matching_count >= self._target_count
        result = SearchBootstrapResult(
            pages_crawled=pages_crawled,
            ads_found=ads_found,
            ads_new=ads_new,
            matching_count=matching_count,
            target_reached=target_reached,
        )
        SearchBootstrapMetricsRepository(self._session).record(
            search_id=self._search_id,
            job_id=self._job_id,
            listing_url=listing_url,
            pages_crawled=result.pages_crawled,
            ads_found=result.ads_found,
            ads_new=result.ads_new,
            matching_count=result.matching_count,
        )
        if result.ads_new > 0:
            CityTaxonomySync(self._session).sync()
        return result

    def _count_matching(self, search) -> int:
        return len(
            self._ads.list_matching_filter(
                brand=search.brand,
                model=search.model,
                min_year=search.min_year,
                max_price=search.max_price,
                max_mileage=search.max_mileage,
                location=search.location,
                limit=self._target_count + 1,
            )
        )

    def _fetch_detail(self, card: ListingCard, detail_parser: DetailParser) -> Optional[AdDraft]:
        html = self._fetcher.fetch(card.url)
        if not html:
            return None
        return detail_parser.parse(html, url=card.url, bama_id=card.bama_id)
