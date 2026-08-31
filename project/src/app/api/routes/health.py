from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services.metrics_service import MetricsService
from app.services.stats_service import StatsService
from config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health_legacy() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/live")
def health_live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
def health_ready(db: Session = Depends(get_db)) -> Response:
    checks: dict[str, str] = {"database": "ok", "redis": "ok"}
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        checks["database"] = str(exc)

    try:
        import redis

        client = redis.from_url(settings.CELERY_BROKER_URL, socket_connect_timeout=2)
        client.ping()
    except Exception as exc:
        checks["redis"] = str(exc)

    if all(value == "ok" for value in checks.values()):
        return Response(
            content='{"status":"ready","checks":' + __import__("json").dumps(checks) + "}",
            media_type="application/json",
            status_code=200,
        )
    return Response(
        content='{"status":"not_ready","checks":' + __import__("json").dumps(checks) + "}",
        media_type="application/json",
        status_code=503,
    )


@router.get("/metrics")
def metrics(db: Session = Depends(get_db)) -> Response:
    body = MetricsService(db).render_prometheus()
    return Response(content=body, media_type="text/plain; version=0.0.4")


@router.get("/admin/stats")
def admin_stats(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    from app.services.stats_service import StatsService, overview_to_dict

    return overview_to_dict(StatsService(db).get_overview())


@router.get("/admin/filter-crawls")
def admin_filter_crawls(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list:
    from app.schemas.crawl import FilterCrawlAdminOut
    from app.services.filter_crawl_service import FilterCrawlService

    rows = FilterCrawlService(db).list_active_for_admin()
    return [FilterCrawlAdminOut.model_validate(row) for row in rows]
