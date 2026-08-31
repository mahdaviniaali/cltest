from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FilterCrawlState(Base):
    __tablename__ = "filter_crawl_states"
    __table_args__ = (
        Index("ix_filter_crawl_states_last_crawl", "last_crawl_at"),
    )

    fingerprint: Mapped[str] = mapped_column(String(64), primary_key=True)
    section_key: Mapped[str] = mapped_column(String(64), nullable=False, default="car")
    listing_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    last_seen_bama_id: Mapped[Optional[str]] = mapped_column(String(128))
    last_crawl_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_job_id: Mapped[Optional[str]] = mapped_column(String(36))
    enabled_search_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    brand: Mapped[Optional[str]] = mapped_column(String(128))
    model: Mapped[Optional[str]] = mapped_column(String(128))
    min_year: Mapped[Optional[int]] = mapped_column(Integer)
    max_price: Mapped[Optional[int]] = mapped_column(Integer)
    max_mileage: Mapped[Optional[int]] = mapped_column(Integer)
    location: Mapped[Optional[str]] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
