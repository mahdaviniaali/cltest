from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.crawl_job import CrawlJob, CrawlJobStatus
from app.models.match import Match
from app.models.notification import Notification, NotificationStatus


class MetricsService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def render_prometheus(self) -> str:
        lines = [
            "# HELP matches_created_total Total matches created",
            "# TYPE matches_created_total counter",
            f"matches_created_total {self._count_matches()}",
            "# HELP notifications_sent_total Notifications sent by channel",
            "# TYPE notifications_sent_total counter",
        ]
        for channel, count in self._notifications_sent_by_channel():
            lines.append(f'notifications_sent_total{{channel="{channel}"}} {count}')
        lines.extend(
            [
                "# HELP crawl_jobs_failed_total Failed crawl jobs",
                "# TYPE crawl_jobs_failed_total counter",
                f"crawl_jobs_failed_total {self._count_failed_jobs()}",
            ]
        )
        return "\n".join(lines) + "\n"

    def _count_matches(self) -> int:
        return int(self._session.scalar(select(func.count()).select_from(Match)) or 0)

    def _count_failed_jobs(self) -> int:
        return int(
            self._session.scalar(
                select(func.count())
                .select_from(CrawlJob)
                .where(CrawlJob.status == CrawlJobStatus.FAILED.value)
            )
            or 0
        )

    def _notifications_sent_by_channel(self) -> list[tuple[str, int]]:
        rows = self._session.execute(
            select(Notification.channel, func.count())
            .where(Notification.status == NotificationStatus.SENT.value)
            .group_by(Notification.channel)
        ).all()
        return [(str(channel), int(count)) for channel, count in rows]
