from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Match(Base):
    __tablename__ = "matches"
    __table_args__ = (UniqueConstraint("ad_id", "search_id", name="uq_matches_ad_search"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ad_id: Mapped[int] = mapped_column(ForeignKey("advertisements.id", ondelete="CASCADE"), nullable=False)
    search_id: Mapped[int] = mapped_column(ForeignKey("searches.id", ondelete="CASCADE"), nullable=False)
    matched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
