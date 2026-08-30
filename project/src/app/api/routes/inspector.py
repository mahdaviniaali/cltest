from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.crawl_job import CrawlJobType
from app.models.user import User
from app.repositories.crawl_event_repository import CrawlEventRepository
from app.repositories.crawl_job_repository import CrawlJobRepository
from app.repositories.site_section_repository import SiteSectionRepository
from app.schemas.inspector import (
    CrawlEventResponse,
    SiteGraphResponse,
    SiteMapJobResponse,
    SiteMapStartRequest,
    SiteNodeSummary,
    SitePageDetail,
    SiteSectionResponse,
    SiteTreeNode,
)
from app.services.inspector import InspectorService
from app.workers.tasks.crawl import site_map_crawl

router = APIRouter(prefix="/inspector", tags=["inspector"])


def _job_response(job) -> SiteMapJobResponse:
    return SiteMapJobResponse(
        job_id=job.id,
        status=job.status,
        job_type=job.job_type,
        pages_crawled=job.pages_crawled,
        pages_discovered=job.pages_discovered,
        pages_failed=job.pages_failed,
        started_at=job.started_at.isoformat() if job.started_at else None,
        finished_at=job.finished_at.isoformat() if job.finished_at else None,
        error=job.error,
    )


def _node_summary(node) -> SiteNodeSummary:
    return SiteNodeSummary(
        page_key=node.page_key,
        url=node.url,
        url_pattern=node.url_pattern,
        depth=node.depth,
        page_type=node.page_type,
        section=node.section,
        title=node.title,
        status=node.status,
    )


@router.post("/site-map/start", response_model=SiteMapJobResponse)
def start_site_map(
    body: SiteMapStartRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SiteMapJobResponse:
    service = InspectorService(db)
    job, already_running = service.start_site_map(
        triggered_by=f"user:{user.id}",
        max_pages=body.max_pages,
        max_depth=body.max_depth,
    )
    if not already_running:
        site_map_crawl.delay(job.id, max_pages=body.max_pages, max_depth=body.max_depth)
    return _job_response(job)


@router.get("/jobs", response_model=list[SiteMapJobResponse])
def list_jobs(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[SiteMapJobResponse]:
    jobs = CrawlJobRepository(db).list_site_map_jobs()
    return [_job_response(j) for j in jobs]


@router.get("/jobs/{job_id}", response_model=SiteMapJobResponse)
def get_job(
    job_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> SiteMapJobResponse:
    job = CrawlJobRepository(db).get(job_id)
    if job is None or job.job_type != CrawlJobType.SITE_MAP.value:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_response(job)


@router.post("/jobs/{job_id}/pause", response_model=SiteMapJobResponse)
def pause_job(
    job_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> SiteMapJobResponse:
    job = InspectorService(db).pause_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    db.commit()
    return _job_response(job)


@router.post("/jobs/{job_id}/resume", response_model=SiteMapJobResponse)
def resume_job(
    job_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SiteMapJobResponse:
    service = InspectorService(db)
    job = service.resume_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    db.commit()
    site_map_crawl.delay(job.id)
    return _job_response(job)


@router.post("/jobs/{job_id}/cancel", response_model=SiteMapJobResponse)
def cancel_job(
    job_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> SiteMapJobResponse:
    job = InspectorService(db).cancel_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    db.commit()
    return _job_response(job)


@router.get("/jobs/{job_id}/events", response_model=list[CrawlEventResponse])
def list_events(
    job_id: str,
    since_id: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[CrawlEventResponse]:
    events = CrawlEventRepository(db).list_since(job_id, since_id=since_id)
    return [
        CrawlEventResponse(
            id=e.id,
            event_type=e.event_type,
            payload=e.payload or {},
            created_at=e.created_at.isoformat(),
        )
        for e in events
    ]


@router.get("/site/tree", response_model=list[SiteTreeNode])
def site_tree(
    section: Optional[str] = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[SiteTreeNode]:
    return InspectorService(db).build_tree(section=section)


@router.get("/site/graph", response_model=SiteGraphResponse)
def site_graph(
    section: Optional[str] = None,
    limit: int = Query(500, ge=1, le=5000),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> SiteGraphResponse:
    nodes, edges = InspectorService(db).build_graph(section=section, limit=limit)
    return SiteGraphResponse(
        nodes=[_node_summary(n) for n in nodes],
        edges=edges,
    )


@router.get("/site/sections", response_model=list[SiteSectionResponse])
def site_sections(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[SiteSectionResponse]:
    sections = SiteSectionRepository(db).list_all()
    return [
        SiteSectionResponse(
            section_key=s.section_key,
            label=s.label,
            root_urls=s.root_urls or [],
            url_patterns=s.url_patterns or [],
            page_count=s.page_count,
            useful_score=s.useful_score,
        )
        for s in sections
    ]


@router.get("/pages/{page_key}", response_model=SitePageDetail)
def page_detail(
    page_key: str,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> SitePageDetail:
    detail = InspectorService(db).get_page_detail(page_key)
    if detail is None:
        raise HTTPException(status_code=404, detail="Page not found")
    node = detail["node"]
    return SitePageDetail(
        page_key=node.page_key,
        url=node.url,
        url_pattern=node.url_pattern,
        depth=node.depth,
        parent_page_key=node.parent_page_key,
        page_type=node.page_type,
        section=node.section,
        title=node.title,
        excerpt=node.excerpt,
        status=node.status,
        meta=node.meta,
        outbound_links=detail["outbound_links"],
    )
