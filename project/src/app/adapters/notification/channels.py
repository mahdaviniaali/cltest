from __future__ import annotations

import logging

from app.domain.notification_ports import NotificationMessage, SendResult

logger = logging.getLogger(__name__)


class InAppChannel:
    channel_id = "in_app"

    def send(self, *, delivery_id: int, message: NotificationMessage) -> SendResult:
        return SendResult(ok=True)


class LogChannel:
    channel_id = "log"

    def send(self, *, delivery_id: int, message: NotificationMessage) -> SendResult:
        logger.info(
            "NOTIFY delivery=%s title=%s url=%s body=%s",
            delivery_id,
            message.title,
            message.ad_url,
            message.body.replace("\n", " | "),
        )
        return SendResult(ok=True)


class NotConfiguredError(Exception):
    pass


class EmailChannel:
    channel_id = "email"

    def send(self, *, delivery_id: int, message: NotificationMessage) -> SendResult:
        from config import settings

        if not settings.smtp_configured():
            return SendResult(ok=False, error="email channel not configured")
        return SendResult(ok=False, error="email adapter stub — configure SMTP in a future release")


class SmsChannel:
    channel_id = "sms"

    def send(self, *, delivery_id: int, message: NotificationMessage) -> SendResult:
        from config import settings

        if not settings.sms_configured():
            return SendResult(ok=False, error="sms channel not configured")
        return SendResult(ok=False, error="sms adapter stub — configure SMS provider in a future release")


class TelegramChannel:
    channel_id = "telegram"

    def send(self, *, delivery_id: int, message: NotificationMessage) -> SendResult:
        from config import settings

        if not settings.telegram_configured():
            return SendResult(ok=False, error="telegram channel not configured")
        return SendResult(ok=False, error="telegram adapter stub — configure TELEGRAM_BOT_TOKEN in a future release")


class ChannelRegistry:
    def __init__(self) -> None:
        self._channels = {
            InAppChannel.channel_id: InAppChannel(),
            LogChannel.channel_id: LogChannel(),
            EmailChannel.channel_id: EmailChannel(),
            SmsChannel.channel_id: SmsChannel(),
            TelegramChannel.channel_id: TelegramChannel(),
        }

    def get(self, channel_id: str):
        return self._channels.get(channel_id)
