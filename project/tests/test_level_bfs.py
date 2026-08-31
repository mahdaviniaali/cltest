from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.repositories.crawl_job_repository import CrawlJobRepository
from config.bama_site import BamaSiteConfig, SectionRoot
from crawler.application.site_map_crawl import SiteMapCrawlService
from crawler.domain.ports import PageFetcher


class FakeFetcher(PageFetcher):
    def __init__(self, pages: dict[str, str]) -> None:
        self._pages = pages
        self.calls: list[str] = []

    def fetch(self, url: str) -> str | None:
        self.calls.append(url)
        for key, html in self._pages.items():
            if url.rstrip("/") == key.rstrip("/") or url.split("?")[0] == key.split("?")[0]:
                return html
        return self._pages.get(url)


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    import app.models.advertisement  # noqa: F401
    import app.models.crawl_job  # noqa: F401
    import app.models.search  # noqa: F401
    import app.models.site_map  # noqa: F401
    import app.models.user  # noqa: F401

    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_level_bfs_section_roots_before_depth_two(db_session):
    job_id = str(uuid4())
    CrawlJobRepository(db_session).create(
        job_type="site_map",
        triggered_by="test",
        idempotency_key=f"bfs:{job_id}",
        job_id=job_id,
    )
    db_session.commit()

    html_home = """
    <html><head><title>Home</title></head><body>
    <a href="https://bama.ir/car/bmw">BMW deep</a>
    </body></html>
    """
    html_car = "<html><head><title>Car</title></head><body><a href='/car/bmw'>BMW</a></body></html>"
    html_moto = "<html><head><title>Moto</title></head><body></body></html>"
    html_truck = "<html><head><title>Truck</title></head><body></body></html>"
    html_bmw = "<html><head><title>BMW</title></head><body></body></html>"

    pages = {
        "https://bama.ir/": html_home,
        "https://bama.ir/car": html_car,
        "https://bama.ir/motorcycle": html_moto,
        "https://bama.ir/truck": html_truck,
        "https://bama.ir/car/bmw": html_bmw,
    }
    config = BamaSiteConfig(
        seed_urls=["https://bama.ir/"],
        domain_allow=["bama.ir"],
        section_roots=[
            SectionRoot(url="https://bama.ir/car", section="car", weight=10),
            SectionRoot(url="https://bama.ir/motorcycle", section="motorcycle", weight=10),
            SectionRoot(url="https://bama.ir/truck", section="truck", weight=10),
        ],
        default_max_depth=4,
        default_max_pages=10,
        sitemap_max_urls=0,
    )
    fetcher = FakeFetcher(pages)
    service = SiteMapCrawlService(
        db_session,
        fetcher,
        job_id=job_id,
        config=config,
        max_pages=6,
        max_depth=4,
    )
    result = service.run()

    assert result.pages_crawled >= 4
    assert fetcher.calls[0] == "https://bama.ir/"
    depth_one_urls = {"https://bama.ir/car", "https://bama.ir/motorcycle", "https://bama.ir/truck"}
    first_sections = fetcher.calls[1:4]
    assert set(first_sections) == depth_one_urls
    assert "https://bama.ir/car/bmw" in fetcher.calls
    assert fetcher.calls.index("https://bama.ir/car/bmw") > max(
        fetcher.calls.index(u) for u in depth_one_urls if u in fetcher.calls
    )
