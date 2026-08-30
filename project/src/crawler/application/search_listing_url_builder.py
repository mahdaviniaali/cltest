from __future__ import annotations

import re
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.models.search import Search
from app.repositories.site_node_repository import SiteNodeRepository
from config import settings
from crawler.application.listing_url_resolver import resolve_listing_url

_SLUG_SAFE = re.compile(r"[^a-z0-9\u0600-\u06ff-]+", re.I)


def _slug(text: str) -> str:
    cleaned = _SLUG_SAFE.sub("-", text.strip().lower())
    return cleaned.strip("-") or text.strip().lower()


def build_search_listing_url(session: Session, search: Search, *, section: str = "car") -> str:
    """Build a scoped Bama listing URL from search filters and site catalog."""
    base = resolve_listing_url(session, section).rstrip("/")

    if search.model:
        model_slug = _slug(search.model)
        nodes = SiteNodeRepository(session).list_all(section=section, limit=5000)
        for node in nodes:
            path = urlparse(node.url).path.lower()
            title = (node.title or "").lower()
            model_lower = search.model.lower()
            if model_lower in path or model_lower in title:
                parts = [p for p in path.split("/") if p]
                if len(parts) >= 2 and parts[0] == section:
                    return f"https://bama.ir/{'/'.join(parts[: min(len(parts), 3)])}"

        if search.brand:
            brand_slug = _slug(search.brand)
            return f"{base}/{brand_slug}/{model_slug}"
        return f"{base}/{model_slug}"

    if search.brand:
        brand_slug = _slug(search.brand)
        nodes = SiteNodeRepository(session).list_all(section=section, limit=5000)
        for node in nodes:
            path = urlparse(node.url).path.lower()
            brand_lower = search.brand.lower()
            if brand_lower in path or brand_lower in (node.title or "").lower():
                parts = [p for p in path.split("/") if p]
                if len(parts) >= 2 and parts[0] == section:
                    return f"https://bama.ir/{'/'.join(parts[:2])}"
        return f"{base}/{brand_slug}"

    return base or settings.BAMA_LISTING_URL
