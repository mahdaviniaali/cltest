from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.site_map import VisitedUrl, VisitedUrlStatus


class VisitedUrlRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def is_visited(self, page_key: str) -> bool:
        stmt = select(VisitedUrl.id).where(
            VisitedUrl.page_key == page_key,
            VisitedUrl.status.in_(
                [VisitedUrlStatus.CRAWLED.value, VisitedUrlStatus.SKIPPED.value]
            ),
        ).limit(1)
        return self._session.scalar(stmt) is not None

    def mark_pending(
        self,
        *,
        url: str,
        page_key: str,
        job_id: str,
        depth: int,
    ) -> VisitedUrl:
        existing = self._session.scalar(
            select(VisitedUrl).where(
                VisitedUrl.job_id == job_id,
                VisitedUrl.page_key == page_key,
            )
        )
        if existing:
            return existing
        row = VisitedUrl(
            url=url,
            page_key=page_key,
            job_id=job_id,
            status=VisitedUrlStatus.PENDING.value,
            depth=depth,
        )
        self._session.add(row)
        self._session.flush()
        return row

    def mark_crawled(self, page_key: str, job_id: str) -> None:
        row = self._session.scalar(
            select(VisitedUrl).where(
                VisitedUrl.job_id == job_id,
                VisitedUrl.page_key == page_key,
            )
        )
        if row:
            row.status = VisitedUrlStatus.CRAWLED.value
            row.crawled_at = datetime.now(timezone.utc)
            self._session.flush()

    def mark_failed(self, page_key: str, job_id: str, error: str) -> None:
        row = self._session.scalar(
            select(VisitedUrl).where(
                VisitedUrl.job_id == job_id,
                VisitedUrl.page_key == page_key,
            )
        )
        if row:
            row.status = VisitedUrlStatus.FAILED.value
            row.error = error
            row.crawled_at = datetime.now(timezone.utc)
            self._session.flush()

    def mark_skipped(self, page_key: str, job_id: str) -> None:
        row = self._session.scalar(
            select(VisitedUrl).where(
                VisitedUrl.job_id == job_id,
                VisitedUrl.page_key == page_key,
            )
        )
        if row:
            row.status = VisitedUrlStatus.SKIPPED.value
            row.crawled_at = datetime.now(timezone.utc)
            self._session.flush()

    def list_pending(self, job_id: str) -> list[VisitedUrl]:
        stmt = (
            select(VisitedUrl)
            .where(
                VisitedUrl.job_id == job_id,
                VisitedUrl.status == VisitedUrlStatus.PENDING.value,
            )
            .order_by(VisitedUrl.depth, VisitedUrl.id)
        )
        return list(self._session.scalars(stmt).all())
