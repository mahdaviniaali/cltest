from __future__ import annotations

from app.models.user import User
from config import settings


class ChannelPolicy:
    def resolve_channels(self, user: User) -> list[str]:
        enabled = set(settings.notification_channels_enabled())
        requested = user.notification_channels or ["in_app"]
        channels: list[str] = []
        for channel in requested:
            if channel not in enabled:
                continue
            if not self._user_supports_channel(user, channel):
                continue
            if channel not in channels:
                channels.append(channel)
        if "in_app" in enabled and "in_app" not in channels:
            channels.insert(0, "in_app")
        return channels

    def _user_supports_channel(self, user: User, channel: str) -> bool:
        if channel == "in_app":
            return True
        if channel == "log":
            return settings.NOTIFICATION_LOG_ENABLED
        if channel == "email":
            return settings.smtp_configured() and "email" in (user.notification_channels or [])
        if channel == "sms":
            return settings.sms_configured() and bool(user.phone)
        if channel == "telegram":
            return settings.telegram_configured() and bool(user.telegram_chat_id)
        return False
