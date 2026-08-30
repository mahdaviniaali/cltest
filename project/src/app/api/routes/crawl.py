from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.repositories.crawl_job_repository import CrawlJobRepository
from app.repositories.crawler_state_repository import CrawlerStateRepository
from app.schemas.crawl import (
    CrawlJobOut,
    CrawlStatusOut,
    CrawlTriggerOut,
    DataStatusOut,
    RefreshOut,
)
from app.services.data_preview import DataPreviewService
from app.services.job_dispatch import dispatch_on_demand_job
from app.services.refresh import RefreshService
from crawler.application.on_demand_crawl import OnDemandCrawlService

router = APIRouter(tags=["crawl"])


@router.post("/crawl/refresh", response_model=RefreshOut, status_code=status.HTTP_202_ACCEPTED)
def refresh_data(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> RefreshOut:
    service = RefreshService(db)
    result = service.request_refresh()
    if result.job_id is not None:
        dispatch_on_demand_job(result.job_id)
    return RefreshOut(is_refreshing=result.is_refreshing, message=result.message)


@router.get("/data/status", response_model=DataStatusOut)
def data_status(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> DataStatusOut:
    last_updated, is_refreshing = DataPreviewService(db).status()
    return DataStatusOut(last_updated_at=last_updated, is_refreshing=is_refreshing)


@router.post("/crawl/trigger", response_model=CrawlTriggerOut, status_code=status.HTTP_202_ACCEPTED)
def trigger_crawl(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> CrawlTriggerOut:
    """Legacy admin-style trigger — prefer POST /crawl/refresh for user UX."""
    service = OnDemandCrawlService(db)
    job_id = service.trigger_global()
    dispatch_on_demand_job(job_id)
    return CrawlTriggerOut(job_id=job_id)


@router.get("/crawl/jobs/{job_id}", response_model=CrawlJobOut)
def get_crawl_job(
    job_id: str,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> CrawlJobOut:
    job = CrawlJobRepository(db).get(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return CrawlJobOut.model_validate(job)


@router.get("/crawl/status", response_model=CrawlStatusOut)
def crawl_status(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> CrawlStatusOut:
    state = CrawlerStateRepository(db).get()
    jobs = CrawlJobRepository(db)
    latest = jobs.latest_completed()
    return CrawlStatusOut(
        last_seen_bama_id=state.last_seen_bama_id if state else None,
        last_crawl_at=state.last_crawl_at if state else None,
        last_run_job_id=state.last_run_job_id if state else None,
        latest_job=CrawlJobOut.model_validate(latest) if latest else None,
    )
