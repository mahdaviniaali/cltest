from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationStatus


class NotificationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_match_channel(self, match_id: int, channel: str) -> Optional[Notification]:
        return self._session.scalar(
            select(Notification).where(
                Notification.match_id == match_id,
                Notification.channel == channel,
            )
        )

    def get_for_user(self, notification_id: int, user_id: int) -> Optional[Notification]:
        return self._session.scalar(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )

    def list_for_user(
        self,
        user_id: int,
        *,
        unread_only: bool = False,
        limit: int = 50,
    ) -> list[Notification]:
        stmt = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            stmt = stmt.where(Notification.read_at.is_(None), Notification.channel == "in_app")
        stmt = stmt.order_by(Notification.created_at.desc()).limit(limit)
        return list(self._session.scalars(stmt).all())

    def unread_count(self, user_id: int) -> int:
        count = self._session.scalar(
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.channel == "in_app",
                Notification.read_at.is_(None),
            )
        )
        return int(count or 0)

    def upsert_delivery(
        self,
        *,
        match_id: int,
        user_id: int,
        channel: str,
        title: str | None,
        body: str | None,
        payload: dict[str, Any] | None,
    ) -> Notification:
        row = self.get_by_match_channel(match_id, channel)
        now = datetime.now(timezone.utc)
        if row is None:
            row = Notification(
                match_id=match_id,
                user_id=user_id,
                channel=channel,
                title=title,
                body=body,
                payload=payload,
                status=NotificationStatus.PENDING.value,
                created_at=now,
            )
            self._session.add(row)
        else:
            if row.title is None and title:
                row.title = title
            if row.body is None and body:
                row.body = body
            if row.payload is None and payload:
                row.payload = payload
        self._session.flush()
        return row

    def mark_sent(self, notification: Notification) -> None:
        now = datetime.now(timezone.utc)
        notification.status = NotificationStatus.SENT.value
        notification.sent_at = now
        self._session.flush()

    def mark_failed(self, notification: Notification, error: str) -> None:
        notification.status = NotificationStatus.FAILED.value
        notification.error = error
        self._session.flush()

    def mark_read(self, notification: Notification) -> None:
        if notification.read_at is not None:
            return
        notification.read_at = datetime.now(timezone.utc)
        self._session.flush()

    def mark_all_read(self, user_id: int) -> int:
        now = datetime.now(timezone.utc)
        rows = list(
            self._session.scalars(
                select(Notification).where(
                    Notification.user_id == user_id,
                    Notification.channel == "in_app",
                    Notification.read_at.is_(None),
                )
            ).all()
        )
        for row in rows:
            row.read_at = now
        self._session.flush()
        return len(rows)
