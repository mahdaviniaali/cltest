from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SearchBase(BaseModel):
    name: Optional[str] = Field(default=None, max_length=128)
    section_key: str = Field(default="car", max_length=64)
    brand: Optional[str] = Field(default=None, max_length=128)
    model: Optional[str] = Field(default=None, max_length=128)
    brand_term_id: Optional[int] = None
    model_term_id: Optional[int] = None
    min_year: Optional[int] = Field(default=None, ge=1300, le=1500)
    max_price: Optional[int] = Field(default=None, ge=0)
    max_mileage: Optional[int] = Field(default=None, ge=0)
    location: Optional[str] = Field(default=None, max_length=256)
    enabled: bool = True


class SearchCreate(SearchBase):
    pass


class SearchUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=128)
    section_key: Optional[str] = Field(default=None, max_length=64)
    brand: Optional[str] = Field(default=None, max_length=128)
    model: Optional[str] = Field(default=None, max_length=128)
    brand_term_id: Optional[int] = None
    model_term_id: Optional[int] = None
    min_year: Optional[int] = Field(default=None, ge=1300, le=1500)
    max_price: Optional[int] = Field(default=None, ge=0)
    max_mileage: Optional[int] = Field(default=None, ge=0)
    location: Optional[str] = Field(default=None, max_length=256)
    enabled: Optional[bool] = None


class SearchOut(SearchBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    bootstrapped_at: Optional[datetime] = None
    last_bootstrap_job_id: Optional[str] = None
    filter_fingerprint: Optional[str] = None

    model_config = {"from_attributes": True}


class SearchCreateOut(SearchOut):
    cached_count: int = 0
    cache_sufficient: bool = False
    is_crawling: bool = False
    job_id: Optional[str] = None


class SearchUpdateOut(SearchCreateOut):
    pass


class SearchRefreshOut(BaseModel):
    is_refreshing: bool = True
    message: str
    job_id: Optional[str] = None
    used_bootstrap: bool = False
