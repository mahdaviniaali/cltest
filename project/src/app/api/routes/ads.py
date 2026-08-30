from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.repositories.advertisement_repository import AdvertisementRepository
from app.schemas.crawl import AdFilterPreview, AdOut, DataPreviewOut

router = APIRouter(prefix="/ads", tags=["ads"])


@router.post("/preview", response_model=DataPreviewOut)
def preview_ads(
    payload: AdFilterPreview,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> DataPreviewOut:
    from app.services.data_preview import DataPreviewService, FilterCriteria

    service = DataPreviewService(db)
    result = service.preview(
        FilterCriteria(
            brand=payload.brand,
            model=payload.model,
            min_year=payload.min_year,
            max_price=payload.max_price,
            max_mileage=payload.max_mileage,
            location=payload.location,
        ),
        limit=payload.limit,
    )
    return DataPreviewOut(
        ads=[AdOut.model_validate(ad) for ad in result.ads],
        total_count=result.total_count,
        last_updated_at=result.last_updated_at,
        is_refreshing=result.is_refreshing,
    )


@router.get("", response_model=list[AdOut])
def list_ads(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[AdOut]:
    repo = AdvertisementRepository(db)
    return [AdOut.model_validate(ad) for ad in repo.list_active(limit=limit, offset=offset)]


@router.get("/{bama_id}", response_model=AdOut)
def get_ad(
    bama_id: str,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> AdOut:
    repo = AdvertisementRepository(db)
    ad = repo.get_by_bama_id(bama_id)
    if ad is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ad not found")
    return AdOut.model_validate(ad)
