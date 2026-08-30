from __future__ import annotations

import logging
import socket
import threading
from typing import Optional
from urllib.parse import urlparse

from config import settings

logger = logging.getLogger(__name__)


def _broker_available(broker_url: str, timeout: float = 0.5) -> bool:
    parsed = urlparse(broker_url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 6379
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def dispatch_site_map_job(
    job_id: str,
    *,
    max_pages: Optional[int] = None,
    max_depth: Optional[int] = None,
) -> str:
    """Enqueue site map via Celery when broker is up; otherwise background thread."""
    if _broker_available(settings.CELERY_BROKER_URL):
        from app.workers.tasks.crawl import site_map_crawl

        try:
            site_map_crawl.delay(job_id, max_pages=max_pages, max_depth=max_depth)
            return "celery"
        except Exception as exc:
            logger.warning("Celery publish failed (%s) — using background thread", exc)

    logger.info("Redis/Celery unavailable — running site map job %s in background thread", job_id)
    thread = threading.Thread(
        target=_run_site_map_in_thread,
        args=(job_id,),
        kwargs={"max_pages": max_pages, "max_depth": max_depth},
        daemon=True,
        name=f"site-map-{job_id[:8]}",
    )
    thread.start()
    return "thread"


def _run_site_map_in_thread(
    job_id: str,
    *,
    max_pages: Optional[int] = None,
    max_depth: Optional[int] = None,
) -> None:
    from app.db.engine import SessionLocal
    from crawler.application.crawl_job_runner import run_site_map_job

    session = SessionLocal()
    try:
        run_site_map_job(session, job_id, max_pages=max_pages, max_depth=max_depth)
    except Exception:
        logger.exception("Background site map job failed: %s", job_id)
    finally:
        session.close()
