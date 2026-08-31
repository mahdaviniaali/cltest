from __future__ import annotations

import re
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.domain.search_filter import model_match_tokens, normalize_for_match
from app.models.search import Search
from app.repositories.site_node_repository import SiteNodeRepository
from config import settings
from crawler.application.listing_url_resolver import resolve_listing_url

_SLUG_SAFE = re.compile(r"[^a-z0-9\u0600-\u06ff-]+", re.I)


def _slug(text: str) -> str:
    cleaned = _SLUG_SAFE.sub("-", text.strip().lower())
    return cleaned.strip("-") or text.strip().lower()


def _node_matches_model(node, model: str, *, section: str) -> bool:
    path = urlparse(node.url).path.lower()
    title = (node.title or "").lower()
    haystack = f"{path} {title}"
    for token in model_match_tokens(model):
        if token in haystack:
            return True
    norm_model = normalize_for_match(model)
    return bool(norm_model and norm_model in haystack)


def _node_matches_brand(node, brand: str, *, section: str) -> bool:
    path = urlparse(node.url).path.lower()
    title = (node.title or "").lower()
    haystack = f"{path} {title}"
    norm_brand = normalize_for_match(brand)
    if not norm_brand:
        return False
    return norm_brand in haystack or haystack in norm_brand


def _listing_url_from_node(node, *, section: str, depth: int = 2) -> str:
    path = urlparse(node.url).path
    parts = [p for p in path.split("/") if p]
    if len(parts) >= 2 and parts[0] == section:
        return f"https://bama.ir/{'/'.join(parts[:depth])}"
    return node.url.split("?")[0]


def build_search_listing_url(session: Session, search: Search, *, section: str = "car") -> str:
    """Build a scoped Bama listing URL from search filters and site catalog."""
    base = resolve_listing_url(session, section).rstrip("/")
    nodes = SiteNodeRepository(session).list_all(section=section, limit=5000)

    if search.model:
        for node in nodes:
            if _node_matches_model(node, search.model, section=section):
                return _listing_url_from_node(node, section=section, depth=3)

        if search.brand:
            brand_slug = _slug(search.brand)
            model_slug = _slug(search.model)
            return f"{base}/{brand_slug}/{model_slug}"
        return f"{base}/{_slug(search.model)}"

    if search.brand:
        for node in nodes:
            if _node_matches_brand(node, search.brand, section=section):
                return _listing_url_from_node(node, section=section, depth=2)
        return f"{base}/{_slug(search.brand)}"

    return base or settings.BAMA_LISTING_URL
