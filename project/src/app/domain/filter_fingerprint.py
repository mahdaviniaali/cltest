from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True, slots=True)
class FilterFingerprint:
    fingerprint: str
    source_key: str
    canonical: dict[str, Any]


def _normalize_value(value: Any) -> Any:
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    return value


def build_filter_canonical(
    *,
    section_key: str = "car",
    brand: Optional[str] = None,
    model: Optional[str] = None,
    brand_term_id: Optional[int] = None,
    model_term_id: Optional[int] = None,
    min_year: Optional[int] = None,
    max_price: Optional[int] = None,
    max_mileage: Optional[int] = None,
    location: Optional[str] = None,
) -> dict[str, Any]:
    return {
        "section_key": section_key or "car",
        "brand": _normalize_value(brand),
        "model": _normalize_value(model),
        "brand_term_id": brand_term_id,
        "model_term_id": model_term_id,
        "min_year": min_year,
        "max_price": max_price,
        "max_mileage": max_mileage,
        "location": _normalize_value(location),
    }


def compute_filter_fingerprint_from_search(search: Any) -> FilterFingerprint:
    return compute_filter_fingerprint(
        section_key=getattr(search, "section_key", None) or "car",
        brand=getattr(search, "brand", None),
        model=getattr(search, "model", None),
        brand_term_id=getattr(search, "brand_term_id", None),
        model_term_id=getattr(search, "model_term_id", None),
        min_year=getattr(search, "min_year", None),
        max_price=getattr(search, "max_price", None),
        max_mileage=getattr(search, "max_mileage", None),
        location=getattr(search, "location", None),
    )


def compute_filter_fingerprint(**criteria: Any) -> FilterFingerprint:
    canonical = build_filter_canonical(**criteria)
    payload = json.dumps(canonical, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    section = canonical["section_key"]
    return FilterFingerprint(
        fingerprint=digest,
        source_key=f"bama:{section}:filter:{digest[:16]}",
        canonical=canonical,
    )
