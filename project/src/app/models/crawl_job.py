from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CrawlJobType(str, enum.Enum):
    SCHEDULED_INCREMENTAL = "scheduled_incremental"
    ON_DEMAND_SEARCH = "on_demand_search"
    ON_DEMAND_GLOBAL = "on_demand_global"


class CrawlJobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CrawlJob(Base):
    __tablename__ = "crawl_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    job_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default=CrawlJobStatus.PENDING.value)
    triggered_by: Mapped[str] = mapped_column(String(64), nullable=False)
    search_id: Mapped[Optional[int]] = mapped_column(ForeignKey("searches.id", ondelete="SET NULL"))
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    pages_crawled: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ads_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ads_new: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
