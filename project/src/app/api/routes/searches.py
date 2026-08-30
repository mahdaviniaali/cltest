from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.repositories.search_repository import SearchRepository
from app.schemas.crawl import AdOut, DataPreviewOut
from app.schemas.search import SearchCreate, SearchCreateOut, SearchOut, SearchRefreshOut, SearchUpdate
from app.services.data_preview import DataPreviewService, FilterCriteria
from app.services.job_dispatch import dispatch_on_demand_job
from app.services.matching import MatchingService
from app.services.search_refresh import SearchRefreshService
from crawler.application.on_demand_crawl import OnDemandCrawlService

router = APIRouter(prefix="/searches", tags=["searches"])


def _search_out(search) -> SearchOut:
    return SearchOut.model_validate(search)


@router.get("", response_model=list[SearchOut])
def list_searches(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SearchOut]:
    repo = SearchRepository(db)
    return [_search_out(item) for item in repo.list_for_user(current_user.id)]


@router.post("", response_model=SearchCreateOut, status_code=status.HTTP_201_CREATED)
def create_search(
    payload: SearchCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SearchCreateOut:
    repo = SearchRepository(db)
    search = repo.create(current_user.id, payload.model_dump())

    on_demand = OnDemandCrawlService(db)
    evaluation = on_demand.evaluate_search(search.id, current_user.id)
    cache = on_demand.evaluate_cache_for_search(search)
    job_id = evaluation.job_id
    is_crawling = False

    if not evaluation.used_cache and job_id:
        dispatch_on_demand_job(job_id)
        is_crawling = True
    else:
        from datetime import datetime, timezone

        if cache.sufficient:
            search.bootstrapped_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(search)
        MatchingService(db).match_existing_for_search(search.id)

    return SearchCreateOut(
        **_search_out(search).model_dump(),
        cached_count=evaluation.cached_count,
        cache_sufficient=cache.sufficient,
        is_crawling=is_crawling,
        job_id=job_id,
    )


@router.get("/{search_id}/results", response_model=DataPreviewOut)
def get_search_results(
    search_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DataPreviewOut:
    repo = SearchRepository(db)
    search = repo.get_for_user(current_user.id, search_id)
    if search is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search not found")

    result = DataPreviewService(db).preview_for_search(search, limit=50)
    return DataPreviewOut(
        ads=[AdOut.model_validate(ad) for ad in result.ads],
        total_count=result.total_count,
        last_updated_at=result.last_updated_at,
        is_refreshing=result.is_refreshing,
        bootstrapped=result.bootstrapped,
        cache_sufficient=result.cache_sufficient,
    )


@router.post("/{search_id}/refresh", response_model=SearchRefreshOut, status_code=status.HTTP_202_ACCEPTED)
def refresh_search(
    search_id: int,
    force: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SearchRefreshOut:
    repo = SearchRepository(db)
    search = repo.get_for_user(current_user.id, search_id)
    if search is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search not found")

    refresh = SearchRefreshService(db).request_refresh(search, force=force)
    if refresh.job_id:
        dispatch_on_demand_job(refresh.job_id)
    return SearchRefreshOut(
        is_refreshing=refresh.is_refreshing,
        message=refresh.message,
        job_id=refresh.job_id,
        used_bootstrap=refresh.used_bootstrap,
    )


@router.get("/{search_id}", response_model=SearchOut)
def get_search(
    search_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SearchOut:
    repo = SearchRepository(db)
    search = repo.get_for_user(current_user.id, search_id)
    if search is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search not found")
    return _search_out(search)


@router.put("/{search_id}", response_model=SearchOut)
def update_search(
    search_id: int,
    payload: SearchUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SearchOut:
    repo = SearchRepository(db)
    search = repo.get_for_user(current_user.id, search_id)
    if search is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search not found")

    data = payload.model_dump(exclude_unset=True)
    updated = repo.update(search, data)
    return _search_out(updated)


@router.delete("/{search_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_search(
    search_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    repo = SearchRepository(db)
    search = repo.get_for_user(current_user.id, search_id)
    if search is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search not found")
    repo.delete(search)


@router.patch("/{search_id}/toggle", response_model=SearchOut)
def toggle_search(
    search_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SearchOut:
    repo = SearchRepository(db)
    search = repo.get_for_user(current_user.id, search_id)
    if search is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search not found")
    updated = repo.toggle_enabled(search)
    return _search_out(updated)
