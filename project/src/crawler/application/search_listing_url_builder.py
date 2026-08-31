from __future__ import annotations

import re
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.domain.search_filter import model_match_tokens, model_matches_filter, normalize_for_match
from app.models.search import Search
from app.repositories.advertisement_repository import AdvertisementRepository
from app.repositories.search_bootstrap_metrics_repository import find_brand_term, find_model_term
from app.repositories.site_node_repository import SiteNodeRepository
from app.repositories.taxonomy_repository import TaxonomyRepository
from config import settings
from crawler.application.listing_url_resolver import resolve_listing_url

_SLUG_SAFE = re.compile(r"[^a-z0-9\u0600-\u06ff-]+", re.I)
_ASCII_SLUG = re.compile(r"^[a-z0-9-]+$")


def _slug(text: str) -> str:
    cleaned = _SLUG_SAFE.sub("-", text.strip().lower())
    return cleaned.strip("-") or text.strip().lower()


def _path_parts(url: str) -> list[str]:
    return [p for p in urlparse(url).path.split("/") if p]


def _canonical_listing_url(section: str, *segments: str) -> str:
    return f"https://bama.ir/{section}/{'/'.join(segments)}"


def _resolve_section(search: Search, section: str | None) -> str:
    return section or getattr(search, "section_key", None) or "car"


def _ascii_slug(text: str | None) -> str | None:
    if not text:
        return None
    cleaned = re.sub(r"[^a-zA-Z0-9-]+", "-", text.strip().lower()).strip("-")
    if cleaned and _ASCII_SLUG.fullmatch(cleaned):
        return cleaned
    return None


def _brand_slug_from_node(node, *, section: str) -> str | None:
    parts = _path_parts(node.url)
    if len(parts) >= 2 and parts[0] == section:
        return parts[1]
    return None


def _extract_model_slug_from_detail_path(url: str, *, section: str, brand_slug: str) -> str | None:
    path = urlparse(url).path.lower()
    prefix = f"/{section}/detail-"
    if not path.startswith(prefix):
        return None
    remainder = path[len(prefix) :].rstrip("/")
    parts = remainder.split("-")
    brand_slug = brand_slug.lower()
    for index, part in enumerate(parts):
        if part == brand_slug and index + 1 < len(parts):
            candidate = parts[index + 1]
            if candidate and not candidate.isdigit() and len(candidate) >= 2:
                return candidate
    return None


def _model_slug_from_ad_urls(
    session: Session,
    search: Search,
    *,
    section: str,
    brand_slug: str,
) -> str | None:
    ads_repo = AdvertisementRepository(session)
    candidates = ads_repo.list_matching_filter(
        brand=search.brand,
        model=search.model,
        limit=20,
    )
    if not candidates:
        candidates = [
            ad
            for ad in ads_repo.list_matching_filter(brand=search.brand, limit=100)
            if model_matches_filter(search.model, ad.model, ad_title=ad.title)
        ]
    for ad in candidates:
        slug = _extract_model_slug_from_detail_path(ad.url, section=section, brand_slug=brand_slug)
        if slug:
            return slug
    return None


def _model_slug_from_site_nodes(
    nodes: list,
    search: Search,
    *,
    section: str,
    brand_slug: str,
) -> str | None:
    prefix = f"/{section}/{brand_slug}/".lower()
    for node in nodes:
        path = urlparse(node.url).path.lower()
        if not path.startswith(prefix):
            continue
        parts = _path_parts(node.url)
        if len(parts) < 3:
            continue
        if _node_matches_model(node, search.model, section=section):
            return parts[2]
    return None


def _resolve_model_slug(
    session: Session,
    search: Search,
    *,
    section: str,
    brand_slug: str,
    nodes: list | None = None,
) -> str | None:
    if not search.model or not brand_slug:
        return None
    node_list = nodes if nodes is not None else SiteNodeRepository(session).list_all(section=section, limit=5000)
    from_site = _model_slug_from_site_nodes(node_list, search, section=section, brand_slug=brand_slug)
    if from_site:
        return from_site
    from_ads = _model_slug_from_ad_urls(session, search, section=section, brand_slug=brand_slug)
    if from_ads:
        return from_ads
    return _ascii_slug(search.model)


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
        if term and term.is_active and term.listing_url and not search.model:
            return term.listing_url

    brand_parent_id: int | None = None
    brand_slug: str | None = None
    if search.brand:
        brand_term = find_brand_term(taxonomy, section, search.brand)
        if brand_term:
            brand_parent_id = brand_term.id
            brand_slug = brand_term.slug if _ascii_slug(brand_term.slug) else None
            if not search.model and brand_term.listing_url:
                return brand_term.listing_url

    if search.model:
        model_term = find_model_term(
            taxonomy,
            section,
            search.model,
            parent_id=brand_parent_id,
        )
        if model_term:
            if model_term.listing_url:
                return model_term.listing_url
            model_slug = model_term.slug if _ascii_slug(model_term.slug) else None
            if brand_slug and model_slug:
                return _canonical_listing_url(section, brand_slug, model_slug)

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


def _find_brand_node(nodes: list, search: Search, *, section: str):
    if not search.brand:
        return None
    for node in nodes:
        if _node_matches_brand(node, search.brand, section=section):
            return node
    return None


def _listing_url_from_nodes(session: Session, search: Search, *, section: str) -> str | None:
    nodes = SiteNodeRepository(session).list_all(section=section, limit=5000)
    brand_node = _find_brand_node(nodes, search, section=section)

    if search.model:
        for node in nodes:
            if _node_matches_model(node, search.model, section=section):
                return _listing_url_from_node(node, section=section, depth=3)
        if brand_node is not None:
            brand_slug = _brand_slug_from_node(brand_node, section=section)
            model_slug = _resolve_model_slug(
                session,
                search,
                section=section,
                brand_slug=brand_slug or "",
                nodes=nodes,
            )
            if brand_slug and model_slug:
                return _canonical_listing_url(section, brand_slug, model_slug)
        return None

    if brand_node is not None:
        return _listing_url_from_node(brand_node, section=section, depth=2)
    return None


def is_brand_only_listing_url(url: str, *, section: str) -> bool:
    parts = _path_parts(url.split("?")[0])
    return len(parts) == 2 and parts[0] == section


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

    if search.model and search.brand:
        nodes = SiteNodeRepository(session).list_all(section=resolved_section, limit=5000)
        brand_node = _find_brand_node(nodes, search, section=resolved_section)
        brand_slug = _brand_slug_from_node(brand_node, section=resolved_section) if brand_node else _ascii_slug(search.brand)
        model_slug = _resolve_model_slug(
            session,
            search,
            section=resolved_section,
            brand_slug=brand_slug or "",
            nodes=nodes,
        )
        if brand_slug and model_slug:
            return _canonical_listing_url(resolved_section, brand_slug, model_slug)
        return f"{base}/{_slug(search.brand)}/{_slug(search.model)}"

    if search.model:
        model_slug = _ascii_slug(search.model) or _slug(search.model)
        return f"{base}/{model_slug}"

    if search.brand:
        return f"{base}/{_slug(search.brand)}"

    return base or settings.BAMA_LISTING_URL
