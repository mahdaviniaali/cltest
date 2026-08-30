from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.notification import Notification, NotificationStatus
from app.models.search import Search

logger = logging.getLogger(__name__)


class NotificationService:
    """MVP notification channel: structured log."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def send_for_match(self, match_id: int) -> bool:
        match = self._session.get(Match, match_id)
        if match is None:
            raise ValueError(f"Match not found: {match_id}")

        existing = self._session.scalar(
            select(Notification).where(Notification.match_id == match_id)
        )
        if existing is not None:
            return existing.status == NotificationStatus.SENT.value

        search = self._session.get(Search, match.search_id)
        if search is None:
            raise ValueError(f"Search not found: {match.search_id}")

        notification = Notification(
            match_id=match_id,
            user_id=search.user_id,
            channel="log",
            status=NotificationStatus.PENDING.value,
        )
        self._session.add(notification)
        self._session.flush()

        try:
            logger.info(
                "NOTIFY user=%s search=%s ad=%s match=%s",
                search.user_id,
                search.id,
                match.ad_id,
                match_id,
            )
            notification.status = NotificationStatus.SENT.value
            notification.sent_at = datetime.now(timezone.utc)
            self._session.flush()
            return True
        except Exception as exc:
            notification.status = NotificationStatus.FAILED.value
            notification.error = str(exc)
            self._session.flush()
            return False
