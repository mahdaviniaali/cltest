from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SearchBase(BaseModel):
    name: Optional[str] = Field(default=None, max_length=128)
    brand: Optional[str] = Field(default=None, max_length=128)
    model: Optional[str] = Field(default=None, max_length=128)
    min_year: Optional[int] = Field(default=None, ge=1300, le=1500)
    max_price: Optional[int] = Field(default=None, ge=0)
    max_mileage: Optional[int] = Field(default=None, ge=0)
    location: Optional[str] = Field(default=None, max_length=256)
    enabled: bool = True


class SearchCreate(SearchBase):
    pass


class SearchUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=128)
    brand: Optional[str] = Field(default=None, max_length=128)
    model: Optional[str] = Field(default=None, max_length=128)
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

    model_config = {"from_attributes": True}
