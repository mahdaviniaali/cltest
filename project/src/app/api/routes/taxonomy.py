from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.repositories.site_section_repository import SiteSectionRepository
from app.repositories.taxonomy_repository import TaxonomyRepository
from app.schemas.taxonomy import TaxonomyCityResponse, TaxonomySectionResponse, TaxonomyTermResponse

router = APIRouter(prefix="/taxonomy", tags=["taxonomy"])


def _term_response(term) -> TaxonomyTermResponse:
    return TaxonomyTermResponse(
        id=term.id,
        section_key=term.section_key,
        term_type=term.term_type,
        parent_id=term.parent_id,
        label=term.label,
        slug=term.slug,
        listing_url=term.listing_url,
        page_key=term.page_key,
        meta=term.meta,
    )


@router.get("/sections", response_model=list[TaxonomySectionResponse])
def list_sections(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[TaxonomySectionResponse]:
    sections = SiteSectionRepository(db).list_all()
    taxonomy = TaxonomyRepository(db)
    brand_counts = taxonomy.count_terms_by_section(term_type="brand")
    model_counts = taxonomy.count_terms_by_section(term_type="model")
    vehicle_sections = [s for s in sections if s.section_key in ("car", "motorcycle", "truck")]
    if not vehicle_sections:
        return [
            TaxonomySectionResponse(
                section_key="car",
                label="خودرو",
                brand_count=brand_counts.get("car", 0),
                model_count=model_counts.get("car", 0),
            ),
            TaxonomySectionResponse(
                section_key="motorcycle",
                label="موتورسیکلت",
                brand_count=brand_counts.get("motorcycle", 0),
                model_count=model_counts.get("motorcycle", 0),
            ),
            TaxonomySectionResponse(
                section_key="truck",
                label="وانت و کامیون",
                brand_count=brand_counts.get("truck", 0),
                model_count=model_counts.get("truck", 0),
            ),
        ]
    return [
        TaxonomySectionResponse(
            section_key=s.section_key,
            label=s.label,
            brand_count=brand_counts.get(s.section_key, 0),
            model_count=model_counts.get(s.section_key, 0),
            page_count=s.page_count,
        )
        for s in vehicle_sections
    ]


@router.get("/brands", response_model=list[TaxonomyTermResponse])
def list_brands(
    section: str = Query(..., min_length=1, max_length=64),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[TaxonomyTermResponse]:
    terms = TaxonomyRepository(db).list_terms(section_key=section, term_type="brand")
    return [_term_response(t) for t in terms]


@router.get("/models", response_model=list[TaxonomyTermResponse])
def list_models(
    section: str = Query(..., min_length=1, max_length=64),
    brand_id: Optional[int] = Query(default=None),
    brand_slug: Optional[str] = Query(default=None, max_length=128),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[TaxonomyTermResponse]:
    repo = TaxonomyRepository(db)
    parent_id = brand_id
    if parent_id is None and brand_slug:
        brand = repo.find_term_by_slug(section_key=section, term_type="brand", slug=brand_slug)
        if brand is None:
            return []
        parent_id = brand.id
    terms = repo.list_terms(section_key=section, term_type="model", parent_id=parent_id)
    return [_term_response(t) for t in terms]


@router.get("/cities", response_model=list[TaxonomyCityResponse])
def list_cities(
    section: str = Query(default="car", min_length=1, max_length=64),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[TaxonomyCityResponse]:
    terms = TaxonomyRepository(db).list_terms(section_key=section, term_type="city")
    return [
        TaxonomyCityResponse(id=t.id, label=t.label, section_key=t.section_key)
        for t in terms
    ]


@router.get("/terms/{term_id}", response_model=TaxonomyTermResponse)
def get_term(
    term_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> TaxonomyTermResponse:
    term = TaxonomyRepository(db).get_term(term_id)
    if term is None or not term.is_active:
        raise HTTPException(status_code=404, detail="Term not found")
    return _term_response(term)
