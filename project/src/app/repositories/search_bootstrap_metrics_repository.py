from __future__ import annotations

from app.domain.search_filter import brand_matches_filter, model_matches_filter, normalize_for_match
from app.models.taxonomy import SearchBootstrapMetric
from app.repositories.taxonomy_repository import TaxonomyRepository


class SearchBootstrapMetricsRepository:
    def __init__(self, session) -> None:
        self._session = session

    def record(
        self,
        *,
        search_id: int,
        job_id: str | None,
        listing_url: str,
        pages_crawled: int,
        ads_found: int,
        ads_new: int,
        matching_count: int,
    ) -> SearchBootstrapMetric:
        row = SearchBootstrapMetric(
            search_id=search_id,
            job_id=job_id,
            listing_url=listing_url,
            pages_crawled=pages_crawled,
            ads_found=ads_found,
            ads_new=ads_new,
            matching_count=matching_count,
        )
        self._session.add(row)
        self._session.flush()
        return row


def find_brand_term(taxonomy: TaxonomyRepository, section: str, brand: str):
    for term in taxonomy.list_terms(section_key=section, term_type="brand"):
        if brand_matches_filter(brand, term.label):
            return term
        if normalize_for_match(brand) == normalize_for_match(term.slug.replace("-", " ")):
            return term
    return None


def find_model_term(
    taxonomy: TaxonomyRepository,
    section: str,
    model: str,
    *,
    parent_id: int | None = None,
):
    terms = taxonomy.list_terms(
        section_key=section,
        term_type="model",
        parent_id=parent_id,
    )
    for term in terms:
        if model_matches_filter(model, term.label):
            return term
        if normalize_for_match(model) == normalize_for_match(term.slug.replace("-", " ")):
            return term
    if parent_id is not None:
        return None
    for term in taxonomy.list_terms(section_key=section, term_type="model"):
        if model_matches_filter(model, term.label):
            return term
    return None
