from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, Protocol


@dataclass(slots=True)
class ListingCard:
    bama_id: str
    url: str
    title: str = ""
    price: Optional[int] = None
    year: Optional[int] = None
    mileage: Optional[int] = None
    location: Optional[str] = None


@dataclass(slots=True)
class AdDraft:
    bama_id: str
    url: str
    title: str
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    price: Optional[int] = None
    mileage: Optional[int] = None
    location: Optional[str] = None
    description: Optional[str] = None
    published_at: Optional[datetime] = None
    raw_data: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class IncrementalCrawlResult:
    pages_crawled: int
    ads_found: int
    ads_new: int
    newest_bama_id: Optional[str]
    stopped_at_checkpoint: bool


@dataclass(slots=True)
class OnDemandCrawlResult:
    used_cache: bool
    job_id: Optional[str]
    cached_count: int = 0
