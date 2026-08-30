from unittest.mock import MagicMock
from uuid import uuid4

from app.models.search import Search
from crawler.application.search_bootstrap_crawl import SearchBootstrapCrawlService
from crawler.domain.entities import AdDraft
from crawler.domain.ports import PageFetcher


class FakeFetcher(PageFetcher):
    def __init__(self, pages: dict[str, str]) -> None:
        self._pages = pages

    def fetch(self, url: str) -> str | None:
        return self._pages.get(url)


class FakeAdStore:
    def __init__(self) -> None:
        self.saved: list[AdDraft] = []

    def save_new(self, draft: AdDraft) -> tuple[int, bool]:
        self.saved.append(draft)
        return len(self.saved), True


def test_bootstrap_crawls_scoped_listing(monkeypatch):
    session = MagicMock()
    search = Search(
        id=1,
        user_id=1,
        brand="Iran Khodro",
        model="Dena",
        enabled=True,
    )
    session.get.return_value = search

    listing_html = """
    <html><body>
    <a href="/car/detail-101">Dena 1</a>
    <a href="/car/detail-102">Dena 2</a>
    </body></html>
    """
    detail_html = "<html><head><title>Iran Khodro Dena</title></head><body></body></html>"

    fetcher = FakeFetcher(
        {
            "https://bama.ir/car/iran-khodro/dena": listing_html,
            "https://bama.ir/car/detail-101": detail_html,
            "https://bama.ir/car/detail-102": detail_html,
        }
    )

    ads_repo = MagicMock()
    ads_repo.list_matching_filter.return_value = []

    service = SearchBootstrapCrawlService(
        session,
        fetcher,
        search_id=1,
        job_id=str(uuid4()),
        max_pages=5,
        target_count=2,
    )
    service._ads = ads_repo
    monkeypatch.setattr(service, "_ad_store", FakeAdStore())

    result = service.run()

    assert result.pages_crawled == 1
    assert result.ads_found == 2
    assert ads_repo.list_matching_filter.called


def test_build_search_listing_url_with_brand_model(monkeypatch):
    from crawler.application.search_listing_url_builder import build_search_listing_url

    session = MagicMock()
    search = Search(id=1, user_id=1, brand="Iran Khodro", model="Dena", enabled=True)
    monkeypatch.setattr(
        "crawler.application.search_listing_url_builder.resolve_listing_url",
        lambda _s, section="car": "https://bama.ir/car",
    )
    monkeypatch.setattr(
        "crawler.application.search_listing_url_builder.SiteNodeRepository",
        lambda _s: MagicMock(list_all=lambda **kwargs: []),
    )

    url = build_search_listing_url(session, search)
    assert "dena" in url.lower()
    assert url.startswith("https://bama.ir/car")
