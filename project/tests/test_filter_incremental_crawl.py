from unittest.mock import MagicMock
from uuid import uuid4

from app.models.filter_crawl_state import FilterCrawlState
from app.models.search import Search
from app.services.filter_crawl_service import FilterCrawlService
from crawler.application.filter_incremental_crawl import FilterIncrementalCrawlService
from tests.fixtures.bama_html import DETAIL_PAGE_1002, DETAIL_PAGE_1003, LISTING_PAGE_1


class FakeFetcher:
    def __init__(self, pages: dict[str, str], details: dict[str, str]) -> None:
        self.pages = pages
        self.details = details

    def fetch(self, url: str) -> str | None:
        if url in self.pages:
            return self.pages[url]
        return self.details.get(url)


def test_filter_incremental_stops_at_checkpoint(db_session, monkeypatch):
    search = Search(user_id=1, brand="Renault", model="Megane", enabled=True)
    db_session.add(search)
    db_session.commit()
    db_session.refresh(search)

    FilterCrawlService(db_session).prepare_search(search)
    fp = search.filter_fingerprint
    listing_url = db_session.get(FilterCrawlState, fp).listing_url

    state = db_session.get(FilterCrawlState, fp)
    state.last_seen_bama_id = "1003-renault-megan"
    db_session.commit()

    fetcher = FakeFetcher(
        pages={listing_url: LISTING_PAGE_1},
        details={"https://bama.ir/car/detail-1003-renault-megan": DETAIL_PAGE_1003},
    )

    service = FilterIncrementalCrawlService(
        db_session,
        fetcher,
        search_id=search.id,
        job_id=str(uuid4()),
    )
    result = service.run()
    assert result.stopped_at_checkpoint is True
    assert result.ads_new == 0


def test_filter_incremental_first_run_sets_checkpoint(db_session, monkeypatch):
    search = Search(user_id=1, brand="Renault", enabled=True)
    db_session.add(search)
    db_session.commit()
    db_session.refresh(search)

    monkeypatch.setattr(
        "crawler.application.filter_listing_url_builder.build_search_listing_url",
        lambda _s, _search: "https://bama.ir/car/renault",
    )
    FilterCrawlService(db_session).prepare_search(search)
    listing_url = db_session.get(FilterCrawlState, search.filter_fingerprint).listing_url

    fetcher = FakeFetcher(
        pages={listing_url: LISTING_PAGE_1},
        details={
            "https://bama.ir/car/detail-1003-renault-megan": DETAIL_PAGE_1003,
            "https://bama.ir/car/detail-1002-renault-megan": DETAIL_PAGE_1002,
        },
    )

    job_id = str(uuid4())
    service = FilterIncrementalCrawlService(
        db_session,
        fetcher,
        search_id=search.id,
        job_id=job_id,
    )
    result = service.run()
    assert result.ads_new == 2
    assert result.newest_bama_id == "1003-renault-megan"

    state = db_session.get(FilterCrawlState, search.filter_fingerprint)
    assert state is not None
    assert state.last_seen_bama_id == "1003-renault-megan"
    assert state.last_crawl_at is not None
