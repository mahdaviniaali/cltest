from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import uuid4

from app.db.engine import SessionLocal
from app.models.crawl_job import CrawlJobType
from app.repositories.crawl_job_repository import CrawlJobRepository
from app.workers.celery_app import celery_app
from config import settings
from crawler.application.crawl_job_runner import run_incremental_job, run_on_demand_job, run_site_map_job

logger = logging.getLogger(__name__)


def _run_scheduled_filter_crawl() -> dict:
    from app.services.filter_crawl_service import FilterCrawlService
    from app.services.job_dispatch import dispatch_on_demand_job

    session = SessionLocal()
    try:
        job_ids = FilterCrawlService(session).enqueue_stale_active_filters()
        for job_id in job_ids:
            dispatch_on_demand_job(job_id)
        return {"enqueued": len(job_ids), "job_ids": job_ids}
    finally:
        session.close()


def _run_scheduled_incremental() -> dict:
    session = SessionLocal()
    try:
        jobs = CrawlJobRepository(session)
        if jobs.get_running_scheduled() is not None:
            logger.info("Skipping scheduled crawl — previous job still running")
            return {"skipped": True}

        bucket = str(int(datetime.now(timezone.utc).timestamp()) // settings.CRAWL_INTERVAL_SECONDS)
        idempotency_key = f"scheduled:{bucket}"
        try:
            job = jobs.create(
                job_type=CrawlJobType.SCHEDULED_INCREMENTAL.value,
                triggered_by="beat",
                idempotency_key=idempotency_key,
            )
            session.commit()
        except Exception:
            session.rollback()
            logger.info("Scheduled crawl already enqueued for bucket %s", bucket)
            return {"skipped": True}

        run_incremental_job(session, job.id)
        return {"job_id": job.id, "status": "completed"}
    finally:
        session.close()


@celery_app.task(name="crawl.scheduled_filter_crawl", bind=True, max_retries=2)
def scheduled_filter_crawl(self) -> dict:
    return _run_scheduled_filter_crawl()


@celery_app.task(name="crawl.scheduled_tick", bind=True, max_retries=2)
def scheduled_tick(self) -> dict:
    return {"filter": _run_scheduled_filter_crawl(), "global": _run_scheduled_incremental()}


@celery_app.task(name="crawl.scheduled_incremental", bind=True, max_retries=2)
def scheduled_incremental(self) -> dict:
    return _run_scheduled_incremental()


@celery_app.task(name="crawl.on_demand", bind=True, max_retries=2)
def on_demand_crawl(self, job_id: str) -> dict:
    session = SessionLocal()
    try:
        run_on_demand_job(session, job_id)
        return {"job_id": job_id, "status": "completed"}
    finally:
        session.close()


@celery_app.task(name="crawl.site_map", bind=True, max_retries=1)
def site_map_crawl(
    self,
    job_id: str,
    max_pages: int | None = None,
    max_depth: int | None = None,
) -> dict:
    session = SessionLocal()
    try:
        run_site_map_job(session, job_id, max_pages=max_pages, max_depth=max_depth)
        job = CrawlJobRepository(session).get(job_id)
        return {"job_id": job_id, "status": job.status if job else "unknown"}
    finally:
        session.close()
