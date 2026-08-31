from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.repositories.search_bootstrap_metrics_repository import find_brand_term, find_model_term
from app.repositories.taxonomy_repository import TaxonomyRepository


def resolve_search_taxonomy(session: Session, data: dict[str, Any]) -> dict[str, Any]:
    """Fill section_key, term IDs, and canonical labels from taxonomy when possible."""
    resolved = dict(data)
    section = resolved.get("section_key") or "car"
    taxonomy = TaxonomyRepository(session)

    brand_term_id = resolved.get("brand_term_id")
    if brand_term_id:
        term = taxonomy.get_term(brand_term_id)
        if term and term.is_active:
            resolved["brand"] = term.label
            section = term.section_key
        else:
            resolved["brand_term_id"] = None
    elif resolved.get("brand"):
        term = find_brand_term(taxonomy, section, resolved["brand"])
        if term:
            resolved["brand_term_id"] = term.id
            resolved["brand"] = term.label
            section = term.section_key
    else:
        resolved["brand_term_id"] = None

    model_term_id = resolved.get("model_term_id")
    parent_id = resolved.get("brand_term_id")
    if model_term_id:
        term = taxonomy.get_term(model_term_id)
        if term and term.is_active:
            resolved["model"] = term.label
            section = term.section_key
            if term.parent_id and not parent_id:
                resolved["brand_term_id"] = term.parent_id
        else:
            resolved["model_term_id"] = None
    elif resolved.get("model"):
        term = find_model_term(
            taxonomy,
            section,
            resolved["model"],
            parent_id=parent_id,
        )
        if term:
            resolved["model_term_id"] = term.id
            resolved["model"] = term.label
            if term.parent_id and not resolved.get("brand_term_id"):
                brand = taxonomy.get_term(term.parent_id)
                if brand:
                    resolved["brand_term_id"] = brand.id
                    resolved["brand"] = brand.label
        else:
            resolved["model_term_id"] = None
    else:
        resolved["model_term_id"] = None

    resolved["section_key"] = section
    return resolved
