from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from app.models.search import Search
from app.repositories.filter_crawl_state_repository import FilterCrawlStateRepository
from app.repositories.search_bootstrap_metrics_repository import SearchBootstrapMetricsRepository
from config import settings
from crawler.adapters.bama.parsers import BamaDetailParser, BamaListingParser
from crawler.adapters.db_ad_store import DbAdStore, DbCrawlCheckpointStore
from crawler.application.filter_listing_url_builder import build_filter_listing_url
from crawler.application.incremental_crawl import IncrementalCrawlService
from crawler.domain.entities import IncrementalCrawlResult
from crawler.domain.ports import PageFetcher

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class FilterIncrementalResult:
    pages_crawled: int
    ads_found: int
    ads_new: int
    newest_bama_id: Optional[str]
    stopped_at_checkpoint: bool
    listing_url: str
    fingerprint: str


class FilterIncrementalCrawlService:
    """Incremental crawl for a canonical user filter (shared checkpoint)."""

    def __init__(
        self,
        session: Session,
        fetcher: PageFetcher,
        *,
        search_id: int,
        job_id: str,
        max_pages: Optional[int] = None,
    ) -> None:
        self._session = session
        self._fetcher = fetcher
        self._search_id = search_id
        self._job_id = job_id
        self._max_pages = max_pages or settings.CRAWL_MAX_PAGES
        self._filter_states = FilterCrawlStateRepository(session)

    def run(self) -> FilterIncrementalResult:
        search = self._session.get(Search, self._search_id)
        if search is None:
            raise ValueError(f"Search not found: {self._search_id}")

        listing = build_filter_listing_url(self._session, search)
        fp = self._filter_states.ensure_fingerprint_on_search(search, listing.url)
        state = self._filter_states.get(fp.fingerprint)
        source_key = fp.source_key

        if state and state.last_seen_bama_id:
            from app.repositories.crawler_state_repository import CrawlerStateRepository

            CrawlerStateRepository(self._session).update_checkpoint(
                last_seen_bama_id=state.last_seen_bama_id,
                job_id=self._job_id,
                source_key=source_key,
            )

        service = IncrementalCrawlService(
            fetcher=self._fetcher,
            listing_parser=BamaListingParser(listing.url),
            detail_parser=BamaDetailParser(),
            ad_store=DbAdStore(self._session),
            checkpoint_store=DbCrawlCheckpointStore(self._session, source_key=source_key),
            listing_url=listing.url,
            max_pages=self._max_pages,
            job_id=self._job_id,
        )
        result: IncrementalCrawlResult = service.run()

        newest = result.newest_bama_id or (state.last_seen_bama_id if state else None)
        if newest:
            self._filter_states.update_checkpoint(
                fp.fingerprint,
                last_seen_bama_id=newest,
                job_id=self._job_id,
                listing_url=listing.url,
            )
        else:
            self._filter_states.touch_crawl(fp.fingerprint, job_id=self._job_id)

        if search.id:
            SearchBootstrapMetricsRepository(self._session).record(
                search_id=search.id,
                job_id=self._job_id,
                listing_url=listing.url,
                pages_crawled=result.pages_crawled,
                ads_found=result.ads_found,
                ads_new=result.ads_new,
                matching_count=result.ads_new,
            )

        state_after = self._filter_states.get(fp.fingerprint)
        if state_after and state_after.last_crawl_at:
            search.bootstrapped_at = search.bootstrapped_at or state_after.last_crawl_at
        search.last_bootstrap_job_id = self._job_id
        self._session.flush()

        return FilterIncrementalResult(
            pages_crawled=result.pages_crawled,
            ads_found=result.ads_found,
            ads_new=result.ads_new,
            newest_bama_id=result.newest_bama_id,
            stopped_at_checkpoint=result.stopped_at_checkpoint,
            listing_url=listing.url,
            fingerprint=fp.fingerprint,
        )
