from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Optional

from crawler.domain.entities import AdDraft, IncrementalCrawlResult, ListingCard
from crawler.domain.ports import (
    AdStore,
    CrawlCheckpointStore,
    DetailParser,
    ListingParser,
    PageFetcher,
)

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[int, int, int], None]


class IncrementalCrawlService:
    """Incremental listing crawl: newest first until checkpoint."""

    def __init__(
        self,
        fetcher: PageFetcher,
        listing_parser: ListingParser,
        detail_parser: DetailParser,
        ad_store: AdStore,
        checkpoint_store: CrawlCheckpointStore,
        *,
        listing_url: str,
        max_pages: int = 10,
        job_id: str,
        on_progress: ProgressCallback | None = None,
    ) -> None:
        self._fetcher = fetcher
        self._listing_parser = listing_parser
        self._detail_parser = detail_parser
        self._ad_store = ad_store
        self._checkpoint = checkpoint_store
        self._listing_url = listing_url
        self._max_pages = max_pages
        self._job_id = job_id
        self._on_progress = on_progress

    def run(self) -> IncrementalCrawlResult:
        last_seen = self._checkpoint.get_last_seen_bama_id()
        pages_crawled = 0
        ads_found = 0
        ads_new = 0
        newest_bama_id: Optional[str] = None
        stopped_at_checkpoint = False
        new_ids_this_run: list[str] = []

        for page in range(1, self._max_pages + 1):
            url = self._listing_parser.next_page_url(self._listing_url, page)
            html = self._fetcher.fetch(url)
            if not html:
                logger.warning("Empty listing page: %s", url)
                break

            pages_crawled += 1
            self._report(pages_crawled, ads_found, ads_new)
            cards = self._listing_parser.parse(html, page=page)
            if not cards:
                break

            if page == 1 and cards:
                candidate_newest = cards[0].bama_id
                if last_seen and candidate_newest == last_seen:
                    stopped_at_checkpoint = True
                    break

            page_new_cards: list[ListingCard] = []
            for card in cards:
                if last_seen and card.bama_id == last_seen:
                    stopped_at_checkpoint = True
                    break
                page_new_cards.append(card)

            for card in page_new_cards:
                ads_found += 1
                if newest_bama_id is None:
                    newest_bama_id = card.bama_id
                new_ids_this_run.append(card.bama_id)
                draft = self._fetch_detail(card)
                if draft is None:
                    continue
                _, created = self._ad_store.save_new(draft)
                if created:
                    ads_new += 1
                self._report(pages_crawled, ads_found, ads_new)

            if stopped_at_checkpoint:
                break

        if new_ids_this_run and newest_bama_id:
            self._checkpoint.update_checkpoint(newest_bama_id, self._job_id)

        return IncrementalCrawlResult(
            pages_crawled=pages_crawled,
            ads_found=ads_found,
            ads_new=ads_new,
            newest_bama_id=newest_bama_id,
            stopped_at_checkpoint=stopped_at_checkpoint,
        )

    def _report(self, pages_crawled: int, ads_found: int, ads_new: int) -> None:
        if self._on_progress is None:
            return
        self._on_progress(pages_crawled, ads_found, ads_new)

    def _fetch_detail(self, card: ListingCard) -> Optional[AdDraft]:
        html = self._fetcher.fetch(card.url)
        if not html:
            return None
        return self._detail_parser.parse(html, url=card.url, bama_id=card.bama_id)
