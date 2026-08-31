"""Incremental crawl dedup stress — FakeFetcher only, no live Bama."""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from app.models.advertisement import Advertisement
from app.models.outbox_event import OutboxEvent
from crawler.adapters.bama.parsers import BamaDetailParser, BamaListingParser
from crawler.adapters.db_ad_store import DbAdStore, DbCrawlCheckpointStore
from crawler.application.incremental_crawl import IncrementalCrawlService
from tests.stress.fake_fetcher import VolumeFakeFetcher
from tests.stress.html_factory import DEFAULT_LISTING_URL, build_crawl_dataset

pytestmark = pytest.mark.stress


def test_incremental_crawl_large_batch(stress_db_session, stress_scale):
    total = stress_scale.crawl_ads
    pages, details = build_crawl_dataset(total, cards_per_page=25)
    fetcher = VolumeFakeFetcher(pages, details)

    service = IncrementalCrawlService(
        fetcher=fetcher,
        listing_parser=BamaListingParser(),
        detail_parser=BamaDetailParser(),
        ad_store=DbAdStore(stress_db_session),
        checkpoint_store=DbCrawlCheckpointStore(stress_db_session),
        listing_url=DEFAULT_LISTING_URL,
        max_pages=(total + 24) // 25,
        job_id="stress-crawl-1",
    )
    result = service.run()

    assert result.ads_new == total
    assert result.pages_crawled >= 1

    ad_count = stress_db_session.scalar(select(func.count()).select_from(Advertisement))
    assert ad_count == total

    outbox_count = stress_db_session.scalar(
        select(func.count()).select_from(OutboxEvent).where(OutboxEvent.event_type == "ad.created")
    )
    assert outbox_count == total


def test_incremental_crawl_second_run_dedups(stress_db_session, stress_scale):
    total = min(stress_scale.crawl_ads, 100)
    pages, details = build_crawl_dataset(total, cards_per_page=20)
    fetcher = VolumeFakeFetcher(pages, details)
    max_pages = (total + 19) // 20

    def run_once(job_id: str):
        return IncrementalCrawlService(
            fetcher=fetcher,
            listing_parser=BamaListingParser(),
            detail_parser=BamaDetailParser(),
            ad_store=DbAdStore(stress_db_session),
            checkpoint_store=DbCrawlCheckpointStore(stress_db_session),
            listing_url=DEFAULT_LISTING_URL,
            max_pages=max_pages,
            job_id=job_id,
        ).run()

    first = run_once("stress-crawl-first")
    assert first.ads_new == total

    second = run_once("stress-crawl-second")
    assert second.ads_new == 0
    assert second.stopped_at_checkpoint is True

    ad_count = stress_db_session.scalar(select(func.count()).select_from(Advertisement))
    assert ad_count == total
