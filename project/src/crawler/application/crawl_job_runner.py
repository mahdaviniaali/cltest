from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.crawl_job import CrawlJobStatus
from app.repositories.crawl_job_repository import CrawlJobRepository
from config import settings
from crawler.adapters.bama.parsers import BamaDetailParser, BamaListingParser
from crawler.adapters.db_ad_store import DbAdStore, DbCrawlCheckpointStore
from crawler.adapters.http_page_fetcher import DelayedPageFetcher, HttpPageFetcher
from crawler.application.incremental_crawl import IncrementalCrawlService
from crawler.core.http_client import HttpClient


def run_incremental_job(session: Session, job_id: str) -> None:
    jobs = CrawlJobRepository(session)
    job = jobs.get(job_id)
    if job is None:
        raise ValueError(f"Job not found: {job_id}")

    jobs.mark_running(job)
    session.commit()

    http = HttpClient(settings.USER_AGENT, timeout=settings.TIMEOUT)
    fetcher = DelayedPageFetcher(
        HttpPageFetcher(http, user_agent=settings.USER_AGENT, respect_robots=True),
        settings.CRAWL_DELAY_SECONDS,
    )
    service = IncrementalCrawlService(
        fetcher=fetcher,
        listing_parser=BamaListingParser(),
        detail_parser=BamaDetailParser(),
        ad_store=DbAdStore(session),
        checkpoint_store=DbCrawlCheckpointStore(session),
        listing_url=settings.BAMA_LISTING_URL,
        max_pages=settings.CRAWL_MAX_PAGES,
        job_id=job_id,
    )

    try:
        result = service.run()
        jobs.mark_completed(
            job,
            pages_crawled=result.pages_crawled,
            ads_found=result.ads_found,
            ads_new=result.ads_new,
        )
        session.commit()
    except Exception as exc:
        jobs.mark_failed(job, str(exc))
        session.commit()
        raise
    finally:
        http.close()
