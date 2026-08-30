from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.repositories.search_repository import SearchRepository
from app.schemas.search import SearchCreate, SearchOut, SearchUpdate
from app.workers.tasks.crawl import on_demand_crawl
from crawler.application.on_demand_crawl import OnDemandCrawlService

router = APIRouter(prefix="/searches", tags=["searches"])


@router.get("", response_model=list[SearchOut])
def list_searches(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SearchOut]:
    repo = SearchRepository(db)
    return [SearchOut.model_validate(item) for item in repo.list_for_user(current_user.id)]


@router.post("", response_model=SearchOut, status_code=status.HTTP_201_CREATED)
def create_search(
    payload: SearchCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SearchOut:
    repo = SearchRepository(db)
    search = repo.create(current_user.id, payload.model_dump())

    on_demand = OnDemandCrawlService(db)
    try:
        result = on_demand.evaluate_search(search.id, current_user.id)
        if not result.used_cache and result.job_id:
            on_demand_crawl.delay(result.job_id)
    except ValueError:
        pass

    return SearchOut.model_validate(search)


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
    return SearchOut.model_validate(search)


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
    return SearchOut.model_validate(updated)


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
    return SearchOut.model_validate(updated)
