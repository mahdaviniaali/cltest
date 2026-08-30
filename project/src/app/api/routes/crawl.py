from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.repositories.crawl_job_repository import CrawlJobRepository
from app.repositories.crawler_state_repository import CrawlerStateRepository
from app.schemas.crawl import CrawlJobOut, CrawlStatusOut, CrawlTriggerOut
from app.workers.tasks.crawl import on_demand_crawl
from crawler.application.on_demand_crawl import OnDemandCrawlService

router = APIRouter(prefix="/crawl", tags=["crawl"])


@router.post("/trigger", response_model=CrawlTriggerOut, status_code=status.HTTP_202_ACCEPTED)
def trigger_crawl(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> CrawlTriggerOut:
    service = OnDemandCrawlService(db)
    job_id = service.trigger_global()
    on_demand_crawl.delay(job_id)
    return CrawlTriggerOut(job_id=job_id)


@router.get("/jobs/{job_id}", response_model=CrawlJobOut)
def get_crawl_job(
    job_id: str,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> CrawlJobOut:
    job = CrawlJobRepository(db).get(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return CrawlJobOut.model_validate(job)


@router.get("/status", response_model=CrawlStatusOut)
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
