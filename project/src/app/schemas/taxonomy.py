from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class TaxonomySectionResponse(BaseModel):
    section_key: str
    label: str
    brand_count: int = 0
    model_count: int = 0
    page_count: int = 0


class TaxonomyTermResponse(BaseModel):
    id: int
    section_key: str
    term_type: str
    parent_id: Optional[int] = None
    label: str
    slug: str
    listing_url: Optional[str] = None
    page_key: Optional[str] = None
    meta: Optional[dict[str, Any]] = None


class TaxonomyCityResponse(BaseModel):
    id: int
    label: str
    section_key: str


class TaxonomyHarvestResponse(BaseModel):
    brands: int = 0
    models: int = 0
    snapshot_id: Optional[int] = None
    skipped: bool = False
