from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from sqlalchemy.orm import Session

from app.domain.filter_fingerprint import FilterFingerprint, compute_filter_fingerprint_from_search
from app.models.filter_crawl_state import FilterCrawlState
from app.models.search import Search
from crawler.application.search_listing_url_builder import build_search_listing_url

# Observed on bama.ir listing pages (2026-08 spike).
_BAMA_SORT_NEWEST = "1"


@dataclass(frozen=True, slots=True)
class FilterListingUrl:
    url: str
    fingerprint: FilterFingerprint


def _merge_query(base_url: str, params: dict[str, str]) -> str:
    parsed = urlparse(base_url)
    existing = dict(parse_qsl(parsed.query, keep_blank_values=True))
    existing.update({k: v for k, v in params.items() if v is not None and v != ""})
    query = urlencode(existing)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", query, ""))


def build_bama_query_params(
    *,
    min_year: Optional[int] = None,
    max_price: Optional[int] = None,
    max_mileage: Optional[int] = None,
    location: Optional[str] = None,
) -> dict[str, str]:
    params: dict[str, str] = {"sort": _BAMA_SORT_NEWEST}
    if min_year is not None:
        params["yearFrom"] = str(min_year)
    if max_price is not None:
        params["priceTo"] = str(max_price)
    if max_mileage is not None:
        if max_mileage <= 0:
            params["mileage"] = "0"
        else:
            params["mileageTo"] = str(max_mileage)
    if location:
        params["city"] = location.strip()
    return params


def build_filter_listing_url(session: Session, search: Any) -> FilterListingUrl:
    fingerprint = compute_filter_fingerprint_from_search(search)
    base_path = build_search_listing_url(session, search)
    query_params = build_bama_query_params(
        min_year=getattr(search, "min_year", None),
        max_price=getattr(search, "max_price", None),
        max_mileage=getattr(search, "max_mileage", None),
        location=getattr(search, "location", None),
    )
    url = _merge_query(base_path, query_params)
    return FilterListingUrl(url=url, fingerprint=fingerprint)


def criteria_from_fingerprint_state(state: FilterCrawlState) -> dict[str, Any]:
    return {
        "section_key": state.section_key,
        "brand": state.brand,
        "model": state.model,
        "min_year": state.min_year,
        "max_price": state.max_price,
        "max_mileage": state.max_mileage,
        "location": state.location,
    }
