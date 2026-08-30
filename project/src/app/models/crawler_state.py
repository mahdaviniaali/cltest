from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CrawlerState(Base):
    __tablename__ = "crawler_state"

    source_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    last_seen_bama_id: Mapped[Optional[str]] = mapped_column(String(32))
    last_crawl_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_run_job_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("crawl_jobs.id", ondelete="SET NULL")
    )
