from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(slots=True)
class NotificationMessage:
    title: str
    body: str
    ad_url: str
    ad_id: int
    search_id: int
    search_name: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SendResult:
    ok: bool
    error: str | None = None


class NotificationChannel(Protocol):
    channel_id: str

    def send(self, *, delivery_id: int, message: NotificationMessage) -> SendResult: ...
