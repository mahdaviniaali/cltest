from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Search(Base):
    __tablename__ = "searches"
    __table_args__ = (
        Index("idx_searches_user_id", "user_id"),
        Index("idx_searches_enabled", "enabled"),
        Index("ix_searches_fingerprint_enabled", "filter_fingerprint", "enabled"),
        Index("ix_searches_brand_term_enabled", "brand_term_id", "enabled"),
        Index("ix_searches_brand_enabled", "brand", "enabled"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(128))
    brand: Mapped[Optional[str]] = mapped_column(String(128))
    model: Mapped[Optional[str]] = mapped_column(String(128))
    min_year: Mapped[Optional[int]] = mapped_column(Integer)
    max_price: Mapped[Optional[int]] = mapped_column(BigInteger)
    max_mileage: Mapped[Optional[int]] = mapped_column(Integer)
    location: Mapped[Optional[str]] = mapped_column(String(256))
    section_key: Mapped[str] = mapped_column(String(64), nullable=False, default="car")
    brand_term_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("taxonomy_terms.id", ondelete="SET NULL"),
        nullable=True,
    )
    model_term_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("taxonomy_terms.id", ondelete="SET NULL"),
        nullable=True,
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
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
    bootstrapped_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_bootstrap_job_id: Mapped[Optional[str]] = mapped_column(String(36))
    filter_fingerprint: Mapped[Optional[str]] = mapped_column(String(64), index=True)

    user: Mapped["User"] = relationship(back_populates="searches")
