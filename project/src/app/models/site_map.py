from __future__ import annotations

import enum
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base


class SiteNodeStatus(str, enum.Enum):
    DISCOVERED = "discovered"
    CRAWLED = "crawled"
    FAILED = "failed"
    SKIPPED = "skipped"


class SitePageType(str, enum.Enum):
    HUB = "hub"
    LISTING = "listing"
    DETAIL = "detail"
    STATIC = "static"
    UNKNOWN = "unknown"


class SiteNode(Base):
    __tablename__ = "site_nodes"

    page_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    url_pattern: Mapped[str] = mapped_column(String(512), nullable=False, default="/")
    depth: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    parent_page_key: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    page_type: Mapped[str] = mapped_column(String(32), nullable=False, default=SitePageType.UNKNOWN.value)
    section: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    excerpt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default=SiteNodeStatus.DISCOVERED.value)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    last_crawled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_job_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    meta: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
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


class SiteEdge(Base):
    __tablename__ = "site_edges"
    __table_args__ = (
        Index("ix_site_edges_from_to", "from_page_key", "to_page_key", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    from_page_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    to_page_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    relation_type: Mapped[str] = mapped_column(String(32), nullable=False, default="internal_link")
    job_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class VisitedUrlStatus(str, enum.Enum):
    PENDING = "pending"
    CRAWLED = "crawled"
    FAILED = "failed"
    SKIPPED = "skipped"


class VisitedUrl(Base):
    __tablename__ = "visited_urls"
    __table_args__ = (
        Index("ix_visited_urls_job_status", "job_id", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    page_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("crawl_jobs.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default=VisitedUrlStatus.PENDING.value)
    depth: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    crawled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class CrawlEvent(Base):
    __tablename__ = "crawl_events"
    __table_args__ = (
        Index("ix_crawl_events_job_id", "job_id", "id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("crawl_jobs.id", ondelete="CASCADE"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class SiteMapGroupKind(str, enum.Enum):
    ROOT = "root"
    SECTION = "section"
    PATH_HUB = "path_hub"
    PATTERN_CLUSTER = "pattern_cluster"


class SiteMapGroup(Base):
    __tablename__ = "site_map_groups"
    __table_args__ = (
        Index("ix_site_map_groups_parent", "parent_group_key"),
        Index("ix_site_map_groups_section", "section"),
    )

    group_key: Mapped[str] = mapped_column(String(256), primary_key=True)
    parent_group_key: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    group_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    label: Mapped[str] = mapped_column(String(256), nullable=False)
    section: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    path_prefix: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    url_pattern: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    page_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    weight: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    inbound_link_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    representative_page_key: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    representative_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    depth: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class SiteSection(Base):
    __tablename__ = "site_sections"

    section_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    root_urls: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    url_patterns: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    useful_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
