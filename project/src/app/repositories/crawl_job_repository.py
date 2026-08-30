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

    def get_any_running(self) -> Optional[CrawlJob]:
        stmt = (
            select(CrawlJob)
            .where(CrawlJob.status == CrawlJobStatus.RUNNING.value)
            .order_by(CrawlJob.started_at.desc())
            .limit(1)
        )
        return self._session.scalar(stmt)

    def get_running_site_map(self) -> Optional[CrawlJob]:
        stmt = (
            select(CrawlJob)
            .where(
                CrawlJob.job_type == "site_map",
                CrawlJob.status.in_(
                    [CrawlJobStatus.RUNNING.value, CrawlJobStatus.PAUSED.value]
                ),
            )
            .order_by(CrawlJob.started_at.desc())
            .limit(1)
        )
        return self._session.scalar(stmt)

    def list_site_map_jobs(self, *, limit: int = 20) -> list[CrawlJob]:
        stmt = (
            select(CrawlJob)
            .where(CrawlJob.job_type == "site_map")
            .order_by(CrawlJob.created_at.desc())
            .limit(limit)
        )
        return list(self._session.scalars(stmt).all())

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

    def mark_paused(self, job: CrawlJob) -> CrawlJob:
        job.status = CrawlJobStatus.PAUSED.value
        self._session.flush()
        return job

    def mark_resumed(self, job: CrawlJob) -> CrawlJob:
        job.status = CrawlJobStatus.RUNNING.value
        self._session.flush()
        return job

    def mark_cancelled(self, job: CrawlJob) -> CrawlJob:
        job.status = CrawlJobStatus.CANCELLED.value
        job.finished_at = datetime.now(timezone.utc)
        self._session.flush()
        return job

    def update_site_map_progress(
        self,
        job: CrawlJob,
        *,
        pages_crawled: int,
        pages_discovered: int,
        pages_failed: int,
    ) -> CrawlJob:
        job.pages_crawled = pages_crawled
        job.pages_discovered = pages_discovered
        job.pages_failed = pages_failed
        self._session.flush()
        return job

    def mark_site_map_completed(
        self,
        job: CrawlJob,
        *,
        pages_crawled: int,
        pages_discovered: int,
        pages_failed: int,
    ) -> CrawlJob:
        job.status = CrawlJobStatus.COMPLETED.value
        job.pages_crawled = pages_crawled
        job.pages_discovered = pages_discovered
        job.pages_failed = pages_failed
        job.finished_at = datetime.now(timezone.utc)
        self._session.flush()
        return job

    def latest_completed(self, job_type: Optional[str] = None) -> Optional[CrawlJob]:
        stmt = select(CrawlJob).where(CrawlJob.status == CrawlJobStatus.COMPLETED.value)
        if job_type:
            stmt = stmt.where(CrawlJob.job_type == job_type)
        stmt = stmt.order_by(CrawlJob.finished_at.desc()).limit(1)
        return self._session.scalar(stmt)
