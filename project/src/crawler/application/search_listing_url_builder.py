from __future__ import annotations

import re
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.domain.search_filter import model_match_tokens, normalize_for_match
from app.models.search import Search
from app.repositories.search_bootstrap_metrics_repository import find_brand_term, find_model_term
from app.repositories.site_node_repository import SiteNodeRepository
from app.repositories.taxonomy_repository import TaxonomyRepository
from config import settings
from crawler.application.listing_url_resolver import resolve_listing_url

_SLUG_SAFE = re.compile(r"[^a-z0-9\u0600-\u06ff-]+", re.I)


def _slug(text: str) -> str:
    cleaned = _SLUG_SAFE.sub("-", text.strip().lower())
    return cleaned.strip("-") or text.strip().lower()


def _resolve_section(search: Search, section: str | None) -> str:
    return section or getattr(search, "section_key", None) or "car"


def _listing_url_from_taxonomy(session: Session, search: Search, *, section: str) -> str | None:
    taxonomy = TaxonomyRepository(session)
    model_term_id = getattr(search, "model_term_id", None)
    brand_term_id = getattr(search, "brand_term_id", None)

    if model_term_id:
        term = taxonomy.get_term(model_term_id)
        if term and term.is_active and term.listing_url:
            return term.listing_url

    if brand_term_id:
        term = taxonomy.get_term(brand_term_id)
        if term and term.is_active and term.listing_url:
            return term.listing_url

    brand_parent_id: int | None = None
    if search.brand:
        brand_term = find_brand_term(taxonomy, section, search.brand)
        if brand_term:
            brand_parent_id = brand_term.id
            if not search.model and brand_term.listing_url:
                return brand_term.listing_url

    if search.model:
        model_term = find_model_term(
            taxonomy,
            section,
            search.model,
            parent_id=brand_parent_id,
        )
        if model_term and model_term.listing_url:
            return model_term.listing_url

    return None


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


def _listing_url_from_nodes(session: Session, search: Search, *, section: str) -> str | None:
    nodes = SiteNodeRepository(session).list_all(section=section, limit=5000)
    if search.model:
        for node in nodes:
            if _node_matches_model(node, search.model, section=section):
                return _listing_url_from_node(node, section=section, depth=3)
    if search.brand:
        for node in nodes:
            if _node_matches_brand(node, search.brand, section=section):
                return _listing_url_from_node(node, section=section, depth=2)
    return None


def build_search_listing_url(session: Session, search: Search, *, section: str | None = None) -> str:
    """Build a scoped Bama listing URL from search filters and taxonomy catalog."""
    resolved_section = _resolve_section(search, section)
    base = resolve_listing_url(session, resolved_section).rstrip("/")

    from_taxonomy = _listing_url_from_taxonomy(session, search, section=resolved_section)
    if from_taxonomy:
        return from_taxonomy

    from_nodes = _listing_url_from_nodes(session, search, section=resolved_section)
    if from_nodes:
        return from_nodes

    if search.model:
        if search.brand:
            return f"{base}/{_slug(search.brand)}/{_slug(search.model)}"
        return f"{base}/{_slug(search.model)}"

    if search.brand:
        return f"{base}/{_slug(search.brand)}"

    return base or settings.BAMA_LISTING_URL
