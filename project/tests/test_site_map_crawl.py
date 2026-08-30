from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.crawl_job import CrawlJob, CrawlJobStatus, CrawlJobType
from app.repositories.crawl_job_repository import CrawlJobRepository
from config.bama_site import BamaSiteConfig
from crawler.application.site_map_crawl import SiteMapCrawlService
from crawler.domain.ports import PageFetcher


class FakeFetcher(PageFetcher):
    def __init__(self, pages: dict[str, str]) -> None:
        self._pages = pages
        self.calls: list[str] = []

    def fetch(self, url: str) -> str | None:
        self.calls.append(url)
        return self._pages.get(url)


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    import app.models.crawl_job  # noqa: F401
    import app.models.site_map  # noqa: F401

    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_site_map_bfs_dedup_and_loop_prevention(db_session):
    job_id = str(uuid4())
    jobs = CrawlJobRepository(db_session)
    job = jobs.create(
        job_type=CrawlJobType.SITE_MAP.value,
        triggered_by="test",
        idempotency_key=f"test:{job_id}",
        job_id=job_id,
    )
    db_session.commit()

    html_home = """
    <html><head><title>Bama Home</title></head><body>
    <a href="/car">Car</a>
    <a href="/car">Car duplicate</a>
    </body></html>
    """
    html_car = """
    <html><head><title>Car listings</title></head><body>
    <a href="/car/detail-1">Ad 1</a>
    <a href="/">Home</a>
    </body></html>
    """
    html_detail = "<html><head><title>Detail</title></head><body>Ad</body></html>"

    pages = {
        "https://bama.ir/": html_home,
        "https://bama.ir/car": html_car,
        "https://bama.ir/car/detail-1": html_detail,
    }
    fetcher = FakeFetcher(pages)
    config = BamaSiteConfig(
        seed_urls=["https://bama.ir/"],
        domain_allow=["bama.ir"],
        default_max_depth=3,
        default_max_pages=10,
    )

    service = SiteMapCrawlService(
        db_session,
        fetcher,
        job_id=job_id,
        config=config,
        max_pages=10,
        max_depth=3,
    )
    result = service.run()

    assert result.pages_crawled >= 2
    assert "https://bama.ir/" in fetcher.calls
    assert fetcher.calls.count("https://bama.ir/car") == 1


def test_site_map_pause_stops_crawl(db_session):
    job_id = str(uuid4())
    jobs = CrawlJobRepository(db_session)
    jobs.create(
        job_type=CrawlJobType.SITE_MAP.value,
        triggered_by="test",
        idempotency_key=f"pause:{job_id}",
        job_id=job_id,
    )
    jobs.mark_running(jobs.get(job_id))
    db_session.commit()

    fetcher = MagicMock(spec=PageFetcher)
    fetcher.fetch.return_value = '<html><a href="/a">A</a><a href="/b">B</a></html>'

    config = BamaSiteConfig(seed_urls=["https://bama.ir/"], domain_allow=["bama.ir"])

    service = SiteMapCrawlService(
        db_session,
        fetcher,
        job_id=job_id,
        config=config,
        max_pages=100,
        max_depth=2,
    )

    jobs.mark_paused(jobs.get(job_id))
    db_session.commit()

    result = service.run()
    assert result.stopped_reason == "paused"
