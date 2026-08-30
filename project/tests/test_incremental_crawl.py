from typing import Optional

from crawler.adapters.bama.parsers import BamaDetailParser, BamaListingParser
from crawler.adapters.db_ad_store import DbAdStore, DbCrawlCheckpointStore
from crawler.application.incremental_crawl import IncrementalCrawlService
from crawler.domain.entities import AdDraft
from tests.fixtures.bama_html import DETAIL_PAGE_1002, DETAIL_PAGE_1003, LISTING_PAGE_1, LISTING_PAGE_2


class FakeFetcher:
    def __init__(self, pages: dict[str, str], details: dict[str, str]) -> None:
        self.pages = pages
        self.details = details
        self.calls: list[str] = []

    def fetch(self, url: str) -> Optional[str]:
        self.calls.append(url)
        if url in self.pages:
            return self.pages[url]
        if url in self.details:
            return self.details[url]
        return None


def test_incremental_stops_at_checkpoint(db_session):
    fetcher = FakeFetcher(
        pages={
            "https://bama.ir/car": LISTING_PAGE_1,
        },
        details={
            "https://bama.ir/car/detail-1003-renault-megan": DETAIL_PAGE_1003,
        },
    )
    checkpoint = DbCrawlCheckpointStore(db_session)
    checkpoint.update_checkpoint("1003", "seed-job")

    service = IncrementalCrawlService(
        fetcher=fetcher,
        listing_parser=BamaListingParser(),
        detail_parser=BamaDetailParser(),
        ad_store=DbAdStore(db_session),
        checkpoint_store=checkpoint,
        listing_url="https://bama.ir/car",
        max_pages=3,
        job_id="job-1",
    )
    result = service.run()
    assert result.stopped_at_checkpoint is True
    assert result.ads_new == 0
    assert result.pages_crawled == 1


def test_incremental_collects_new_ads_and_outbox(db_session):
    fetcher = FakeFetcher(
        pages={
            "https://bama.ir/car": LISTING_PAGE_1,
            "https://bama.ir/car?page=2": LISTING_PAGE_2,
        },
        details={
            "https://bama.ir/car/detail-1003-renault-megan": DETAIL_PAGE_1003,
            "https://bama.ir/car/detail-1002-renault-megan": DETAIL_PAGE_1002,
        },
    )
    service = IncrementalCrawlService(
        fetcher=fetcher,
        listing_parser=BamaListingParser(),
        detail_parser=BamaDetailParser(),
        ad_store=DbAdStore(db_session),
        checkpoint_store=DbCrawlCheckpointStore(db_session),
        listing_url="https://bama.ir/car",
        max_pages=2,
        job_id="job-2",
    )
    result = service.run()
    assert result.ads_new == 2
    assert result.newest_bama_id == "1003"

    from app.models.advertisement import Advertisement
    from app.models.outbox_event import OutboxEvent
    from sqlalchemy import select

    ads = list(db_session.scalars(select(Advertisement)))
    events = list(db_session.scalars(select(OutboxEvent)))
    assert len(ads) == 2
    assert len(events) == 2
    assert all(e.event_type == "ad.created" for e in events)

    state = DbCrawlCheckpointStore(db_session).get_last_seen_bama_id()
    assert state == "1003"
