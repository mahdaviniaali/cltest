from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.crawl_job import CrawlJobType
from app.repositories.crawl_job_repository import CrawlJobRepository


REFRESH_MESSAGE = "داده‌ها در حال بروزرسانی هستند"


@dataclass(slots=True)
class RefreshResult:
    is_refreshing: bool
    message: str
    job_id: str | None = None


class RefreshService:
    """Global incremental refresh — neutral UX, idempotent while running."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._jobs = CrawlJobRepository(session)

    def request_refresh(self) -> RefreshResult:
        if self._jobs.get_any_running() is not None:
            return RefreshResult(is_refreshing=True, message=REFRESH_MESSAGE)

        job = self._jobs.create(
            job_type=CrawlJobType.ON_DEMAND_GLOBAL.value,
            triggered_by="user_refresh",
            idempotency_key=f"refresh:{uuid4()}",
        )
        self._session.commit()
        return RefreshResult(
            is_refreshing=True,
            message=REFRESH_MESSAGE,
            job_id=job.id,
        )
