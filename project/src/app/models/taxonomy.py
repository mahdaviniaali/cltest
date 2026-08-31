from __future__ import annotations

import enum
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base


class TaxonomyTermType(str, enum.Enum):
    BRAND = "brand"
    MODEL = "model"
    CITY = "city"


class TaxonomySnapshot(Base):
    __tablename__ = "taxonomy_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_job_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class TaxonomyTerm(Base):
    __tablename__ = "taxonomy_terms"
    __table_args__ = (
        Index("ix_taxonomy_terms_section_type", "section_key", "term_type", "is_active"),
        Index("ix_taxonomy_terms_parent", "parent_id"),
        Index("ix_taxonomy_terms_snapshot", "snapshot_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_id: Mapped[int] = mapped_column(
        ForeignKey("taxonomy_snapshots.id", ondelete="CASCADE"),
        nullable=False,
    )
    section_key: Mapped[str] = mapped_column(String(64), nullable=False)
    term_type: Mapped[str] = mapped_column(String(16), nullable=False)
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("taxonomy_terms.id", ondelete="SET NULL"),
        nullable=True,
    )
    label: Mapped[str] = mapped_column(String(256), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), nullable=False)
    listing_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    page_key: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    meta: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class TaxonomyRef(Base):
    __tablename__ = "taxonomy_refs"
    __table_args__ = (
        Index("ix_taxonomy_refs_term", "term_id"),
        Index("ix_taxonomy_refs_page_key", "page_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    term_id: Mapped[int] = mapped_column(
        ForeignKey("taxonomy_terms.id", ondelete="CASCADE"),
        nullable=False,
    )
    page_key: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    url_pattern: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    source_job_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    extracted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class SearchBootstrapMetric(Base):
    __tablename__ = "search_bootstrap_metrics"
    __table_args__ = (
        Index("ix_search_bootstrap_metrics_search", "search_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    search_id: Mapped[int] = mapped_column(
        ForeignKey("searches.id", ondelete="CASCADE"),
        nullable=False,
    )
    job_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    listing_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    pages_crawled: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ads_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ads_new: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    matching_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
