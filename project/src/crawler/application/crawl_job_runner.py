from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.crawl_job import CrawlJobStatus
from app.repositories.crawl_job_repository import CrawlJobRepository
from config import settings
from crawler.adapters.bama.parsers import BamaDetailParser, BamaListingParser
from crawler.adapters.db_ad_store import DbAdStore, DbCrawlCheckpointStore
from crawler.adapters.http_page_fetcher import DelayedPageFetcher, HttpPageFetcher
from crawler.application.incremental_crawl import IncrementalCrawlService
from crawler.application.listing_url_resolver import resolve_listing_url
from crawler.application.site_map_crawl import SiteMapCrawlService
from crawler.core.http_client import HttpClient
from config.bama_site import load_bama_site_config


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
    listing_url = resolve_listing_url(session, "car")
    service = IncrementalCrawlService(
        fetcher=fetcher,
        listing_parser=BamaListingParser(listing_url),
        detail_parser=BamaDetailParser(),
        ad_store=DbAdStore(session),
        checkpoint_store=DbCrawlCheckpointStore(session),
        listing_url=listing_url,
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


def run_site_map_job(
    session: Session,
    job_id: str,
    *,
    max_pages: int | None = None,
    max_depth: int | None = None,
) -> None:
    jobs = CrawlJobRepository(session)
    job = jobs.get(job_id)
    if job is None:
        raise ValueError(f"Job not found: {job_id}")

    jobs.mark_running(job)
    session.commit()

    config = load_bama_site_config()
    http = HttpClient(settings.USER_AGENT, timeout=settings.TIMEOUT)
    fetcher = DelayedPageFetcher(
        HttpPageFetcher(http, user_agent=settings.USER_AGENT, respect_robots=True),
        settings.SITE_MAP_DELAY_SECONDS,
    )
    service = SiteMapCrawlService(
        session,
        fetcher,
        job_id=job_id,
        config=config,
        max_pages=max_pages or settings.SITE_MAP_MAX_PAGES,
        max_depth=max_depth or settings.SITE_MAP_MAX_DEPTH,
    )

    try:
        result = service.run()
        if result.stopped_reason == "paused":
            jobs.mark_paused(job)
        elif result.stopped_reason == "cancelled":
            jobs.mark_cancelled(job)
        else:
            jobs.mark_site_map_completed(
                job,
                pages_crawled=result.pages_crawled,
                pages_discovered=result.pages_discovered,
                pages_failed=result.pages_failed,
            )
        session.commit()
    except Exception as exc:
        jobs.mark_failed(job, str(exc))
        session.commit()
        raise
    finally:
        http.close()
