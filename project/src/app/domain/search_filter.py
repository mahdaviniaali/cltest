from __future__ import annotations

from typing import Any, Optional


def ad_matches_search_criteria(
    ad: Any,
    *,
    brand: Optional[str] = None,
    model: Optional[str] = None,
    min_year: Optional[int] = None,
    max_price: Optional[int] = None,
    max_mileage: Optional[int] = None,
    location: Optional[str] = None,
) -> bool:
    """Shared filter semantics for matching and validation."""
    if brand and ad.brand and brand.lower() != ad.brand.lower():
        return False
    if model and ad.model and model.lower() != ad.model.lower():
        return False
    if min_year is not None and ad.year is not None and ad.year < min_year:
        return False
    if max_price is not None and ad.price is not None and ad.price > max_price:
        return False
    if max_mileage is not None and ad.mileage is not None and ad.mileage > max_mileage:
        return False
    if location and ad.location and location.lower() not in ad.location.lower():
        return False
    return True
