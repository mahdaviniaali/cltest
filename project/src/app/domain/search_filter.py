from __future__ import annotations

import re
from typing import Any, Optional

from sqlalchemy import func, literal, or_

from crawler.domain.labels import normalize_label

_ARABIC_YE = str.maketrans({"ي": "ی", "ك": "ک"})


def normalize_for_match(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = normalize_label(value)
    if not cleaned:
        return None
    return cleaned.translate(_ARABIC_YE).lower()


def model_match_tokens(model: Optional[str]) -> list[str]:
    norm = normalize_for_match(model)
    if not norm:
        return []
    return [t for t in re.split(r"\s+", norm) if len(t) >= 2]


def brand_matches_filter(filter_brand: Optional[str], ad_brand: Optional[str]) -> bool:
    if not filter_brand:
        return True
    if not ad_brand:
        return True
    needle = normalize_for_match(filter_brand)
    haystack = normalize_for_match(ad_brand)
    if not needle or not haystack:
        return True
    return needle == haystack or needle in haystack or haystack in needle


def model_matches_filter(
    filter_model: Optional[str],
    ad_model: Optional[str],
    *,
    ad_title: Optional[str] = None,
) -> bool:
    if not filter_model:
        return True
    needle = normalize_for_match(filter_model)
    if not needle:
        return True

    haystacks: list[str] = []
    if ad_model:
        haystacks.append(normalize_for_match(ad_model) or "")
    if ad_title:
        haystacks.append(normalize_for_match(ad_title) or "")
    if not haystacks:
        return True

    combined = " ".join(h for h in haystacks if h)
    if needle == combined or needle in combined or combined in needle:
        return True

    ad_model_norm = normalize_for_match(ad_model)
    if ad_model_norm and len(ad_model_norm) >= 2 and ad_model_norm in needle:
        return True

    tokens = model_match_tokens(filter_model)
    if len(tokens) <= 1:
        token = tokens[0] if tokens else needle
        return any(token in h for h in haystacks if h)

    significant = [t for t in tokens if len(t) >= 3] or tokens
    return any(any(t in h for h in haystacks if h) for t in significant)


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
    if not brand_matches_filter(brand, ad.brand):
        return False
    if not model_matches_filter(model, ad.model, ad_title=getattr(ad, "title", None)):
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


def sql_brand_match(column, brand: str):
    """Same rule as brand_matches_filter: either side may be a substring of the other.

    Taxonomy labels are often longer than the H1 brand (e.g. extra Latin), so
    results SQL must not be one-directional.
    """
    norm_brand = normalize_for_match(brand)
    if not norm_brand:
        return None
    return or_(
        column == norm_brand,
        column.like(f"%{norm_brand}%"),
        (column.isnot(None))
        & (column != "")
        & literal(norm_brand).like(func.concat("%", column, "%")),
    )


def sql_model_match(model_col, title_col, model: str):
    norm_model = normalize_for_match(model)
    if not norm_model:
        return None

    tokens = model_match_tokens(model)
    reverse = (
        (model_col.isnot(None))
        & (model_col != "")
        & literal(norm_model).like(func.concat("%", model_col, "%"))
    )
    if len(tokens) <= 1:
        token = tokens[0] if tokens else norm_model
        return or_(
            model_col == token,
            model_col.like(f"%{token}%"),
            title_col.like(f"%{token}%"),
            reverse,
        )

    significant = [t for t in tokens if len(t) >= 3] or tokens
    return or_(
        reverse,
        *[or_(model_col.like(f"%{t}%"), title_col.like(f"%{t}%")) for t in significant],
    )
