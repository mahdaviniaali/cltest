from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import uuid4

from app.db.engine import SessionLocal
from app.models.crawl_job import CrawlJobType
from app.repositories.crawl_job_repository import CrawlJobRepository
from app.workers.celery_app import celery_app
from config import settings
from crawler.application.crawl_job_runner import run_incremental_job

logger = logging.getLogger(__name__)


@celery_app.task(name="crawl.scheduled_incremental", bind=True, max_retries=2)
def scheduled_incremental(self) -> dict:
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


@celery_app.task(name="crawl.on_demand", bind=True, max_retries=2)
def on_demand_crawl(self, job_id: str) -> dict:
    session = SessionLocal()
    try:
        run_incremental_job(session, job_id)
        return {"job_id": job_id, "status": "completed"}
    finally:
        session.close()
