from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: int
    match_id: int
    channel: str
    title: Optional[str] = None
    body: Optional[str] = None
    payload: Optional[dict[str, Any]] = None
    status: str
    read_at: Optional[str] = None
    sent_at: Optional[str] = None
    created_at: str


class UnreadCountOut(BaseModel):
    count: int
