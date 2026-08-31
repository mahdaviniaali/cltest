from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.adapters.notification.channels import ChannelRegistry
from app.domain.channel_policy import ChannelPolicy
from app.models.match import Match
from app.models.user import User
from app.repositories.advertisement_repository import AdvertisementRepository
from app.repositories.notification_repository import NotificationRepository
from app.services.notification_message_builder import NotificationMessageBuilder

logger = logging.getLogger(__name__)


class NotificationOrchestrator:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._ads = AdvertisementRepository(session)
        self._notifications = NotificationRepository(session)
        self._policy = ChannelPolicy()
        self._builder = NotificationMessageBuilder()
        self._registry = ChannelRegistry()

    def orchestrate(self, match_id: int) -> dict:
        match = self._session.get(Match, match_id)
        if match is None:
            raise ValueError(f"Match not found: {match_id}")

        from app.models.search import Search

        search = self._session.get(Search, match.search_id)
        if search is None:
            raise ValueError(f"Search not found: {match.search_id}")

        user = self._session.get(User, search.user_id)
        if user is None:
            raise ValueError(f"User not found: {search.user_id}")

        ad = self._ads.get_by_id(match.ad_id)
        if ad is None:
            raise ValueError(f"Ad not found: {match.ad_id}")

        message = self._builder.build(ad, search)
        channels = self._policy.resolve_channels(user)
        sent = 0
        failed = 0
        skipped = 0

        for channel_id in channels:
            adapter = self._registry.get(channel_id)
            if adapter is None:
                skipped += 1
                continue

            delivery = self._notifications.upsert_delivery(
                match_id=match_id,
                user_id=user.id,
                channel=channel_id,
                title=message.title,
                body=message.body,
                payload={
                    "ad_url": message.ad_url,
                    "ad_id": message.ad_id,
                    "search_id": message.search_id,
                    "search_name": message.search_name,
                    **message.extra,
                },
            )
            if delivery.status == "sent":
                skipped += 1
                continue

            try:
                result = adapter.send(delivery_id=delivery.id, message=message)
                if result.ok:
                    self._notifications.mark_sent(delivery)
                    sent += 1
                else:
                    self._notifications.mark_failed(delivery, result.error or "send failed")
                    failed += 1
            except Exception as exc:
                logger.exception("Notification send failed match=%s channel=%s", match_id, channel_id)
                self._notifications.mark_failed(delivery, str(exc))
                failed += 1

        return {
            "match_id": match_id,
            "channels": channels,
            "sent": sent,
            "failed": failed,
            "skipped": skipped,
        }
