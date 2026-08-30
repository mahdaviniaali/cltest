from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class SiteMapStartRequest(BaseModel):
    max_pages: Optional[int] = Field(None, ge=1, le=50000)
    max_depth: Optional[int] = Field(None, ge=1, le=20)


class SiteMapJobResponse(BaseModel):
    job_id: str
    status: str
    job_type: str
    pages_crawled: int = 0
    pages_discovered: int = 0
    pages_failed: int = 0
    current_depth: int = 0
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    error: Optional[str] = None


class CrawlEventResponse(BaseModel):
    id: int
    event_type: str
    payload: dict[str, Any]
    created_at: str


class SiteNodeSummary(BaseModel):
    page_key: str
    url: str
    url_pattern: str
    depth: int
    page_type: str
    section: Optional[str]
    title: Optional[str]
    status: str


class SiteTreeNode(BaseModel):
    path: str
    label: str
    page_key: Optional[str] = None
    page_type: Optional[str] = None
    section: Optional[str] = None
    children: list["SiteTreeNode"] = Field(default_factory=list)


SiteTreeNode.model_rebuild()


class SiteGraphResponse(BaseModel):
    nodes: list[SiteNodeSummary]
    edges: list[dict[str, str]]


class SiteSectionResponse(BaseModel):
    section_key: str
    label: str
    root_urls: list[str]
    url_patterns: list[str]
    page_count: int
    useful_score: float


class SitePageDetail(BaseModel):
    page_key: str
    url: str
    url_pattern: str
    depth: int
    parent_page_key: Optional[str]
    page_type: str
    section: Optional[str]
    title: Optional[str]
    excerpt: Optional[str]
    status: str
    meta: Optional[dict[str, Any]]
    outbound_links: list[dict[str, str]] = Field(default_factory=list)
