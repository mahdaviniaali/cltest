from datetime import datetime
from typing import Any, Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base


class Advertisement(Base):
    __tablename__ = "advertisements"
    __table_args__ = (
        Index("idx_advertisements_brand_model", "brand", "model"),
        Index("idx_advertisements_year", "year"),
        Index("idx_advertisements_price", "price"),
        Index("idx_advertisements_mileage", "mileage"),
        Index("idx_advertisements_location", "location"),
        Index("idx_advertisements_published_at", "published_at"),
        Index("idx_advertisements_crawled_at", "crawled_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bama_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    url: Mapped[str] = mapped_column(String(512), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)

    brand: Mapped[Optional[str]] = mapped_column(String(128))
    model: Mapped[Optional[str]] = mapped_column(String(128))
    year: Mapped[Optional[int]] = mapped_column(Integer)
    price: Mapped[Optional[int]] = mapped_column(BigInteger)
    mileage: Mapped[Optional[int]] = mapped_column(Integer)
    location: Mapped[Optional[str]] = mapped_column(String(256))

    engine_capacity_cc: Mapped[Optional[int]] = mapped_column(Integer)
    transmission: Mapped[Optional[str]] = mapped_column(String(32))
    fuel_type: Mapped[Optional[str]] = mapped_column(String(32))
    body_type: Mapped[Optional[str]] = mapped_column(String(64))
    body_color: Mapped[Optional[str]] = mapped_column(String(64))
    interior_color: Mapped[Optional[str]] = mapped_column(String(64))
    body_condition: Mapped[Optional[str]] = mapped_column(String(128))

    seller_name: Mapped[Optional[str]] = mapped_column(String(256))
    seller_phone: Mapped[Optional[str]] = mapped_column(String(32))
    seller_address: Mapped[Optional[str]] = mapped_column(String(512))
    description: Mapped[Optional[str]] = mapped_column(Text)

    technical_specs: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    crawled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    raw_data: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)

    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_sold: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
