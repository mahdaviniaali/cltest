from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.crawl_job import CrawlJob, CrawlJobStatus


class CrawlJobRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, job_id: str) -> Optional[CrawlJob]:
        return self._session.get(CrawlJob, job_id)

    def get_running_scheduled(self) -> Optional[CrawlJob]:
        stmt = (
            select(CrawlJob)
            .where(
                CrawlJob.job_type == "scheduled_incremental",
                CrawlJob.status == CrawlJobStatus.RUNNING.value,
            )
            .limit(1)
        )
        return self._session.scalar(stmt)

    def create(
        self,
        *,
        job_type: str,
        triggered_by: str,
        idempotency_key: str,
        search_id: Optional[int] = None,
        job_id: Optional[str] = None,
    ) -> CrawlJob:
        job = CrawlJob(
            id=job_id or str(uuid4()),
            job_type=job_type,
            status=CrawlJobStatus.PENDING.value,
            triggered_by=triggered_by,
            search_id=search_id,
            idempotency_key=idempotency_key,
        )
        self._session.add(job)
        self._session.flush()
        return job

    def mark_running(self, job: CrawlJob) -> CrawlJob:
        job.status = CrawlJobStatus.RUNNING.value
        job.started_at = datetime.now(timezone.utc)
        self._session.flush()
        return job

    def mark_completed(
        self,
        job: CrawlJob,
        *,
        pages_crawled: int,
        ads_found: int,
        ads_new: int,
    ) -> CrawlJob:
        job.status = CrawlJobStatus.COMPLETED.value
        job.pages_crawled = pages_crawled
        job.ads_found = ads_found
        job.ads_new = ads_new
        job.finished_at = datetime.now(timezone.utc)
        self._session.flush()
        return job

    def mark_failed(self, job: CrawlJob, error: str) -> CrawlJob:
        job.status = CrawlJobStatus.FAILED.value
        job.error = error
        job.finished_at = datetime.now(timezone.utc)
        self._session.flush()
        return job

    def latest_completed(self, job_type: Optional[str] = None) -> Optional[CrawlJob]:
        stmt = select(CrawlJob).where(CrawlJob.status == CrawlJobStatus.COMPLETED.value)
        if job_type:
            stmt = stmt.where(CrawlJob.job_type == job_type)
        stmt = stmt.order_by(CrawlJob.finished_at.desc()).limit(1)
        return self._session.scalar(stmt)
