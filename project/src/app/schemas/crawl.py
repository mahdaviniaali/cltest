from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class AdOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bama_id: str
    url: str
    title: str
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    price: Optional[int] = None
    mileage: Optional[int] = None
    location: Optional[str] = None
    crawled_at: datetime


class CrawlJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_type: str
    status: str
    triggered_by: str
    search_id: Optional[int] = None
    pages_crawled: int
    ads_found: int
    ads_new: int
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime


class CrawlStatusOut(BaseModel):
    last_seen_bama_id: Optional[str] = None
    last_crawl_at: Optional[datetime] = None
    last_run_job_id: Optional[str] = None
    latest_job: Optional[CrawlJobOut] = None


class CrawlTriggerOut(BaseModel):
    job_id: str
    message: str = "Crawl job enqueued"


class SearchCreateResponse(BaseModel):
    search: Any
    crawl: Optional[dict[str, Any]] = None
