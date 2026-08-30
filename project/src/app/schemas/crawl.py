from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


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


class AdFilterPreview(BaseModel):
    brand: Optional[str] = Field(default=None, max_length=128)
    model: Optional[str] = Field(default=None, max_length=128)
    min_year: Optional[int] = Field(default=None, ge=1300, le=1500)
    max_price: Optional[int] = Field(default=None, ge=0)
    max_mileage: Optional[int] = Field(default=None, ge=0)
    location: Optional[str] = Field(default=None, max_length=256)
    limit: int = Field(default=20, ge=1, le=100)


class DataPreviewOut(BaseModel):
    ads: list[AdOut]
    total_count: int
    last_updated_at: Optional[datetime] = None
    is_refreshing: bool


class DataStatusOut(BaseModel):
    last_updated_at: Optional[datetime] = None
    is_refreshing: bool


class RefreshOut(BaseModel):
    is_refreshing: bool = True
    message: str = "داده‌ها در حال بروزرسانی هستند"


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
