from __future__ import annotations

import logging
import threading
from typing import Optional

logger = logging.getLogger(__name__)


def dispatch_site_map_job(
    job_id: str,
    *,
    max_pages: Optional[int] = None,
    max_depth: Optional[int] = None,
) -> str:
    """Enqueue site map job via Celery; fall back to in-process thread if broker is down."""
    from app.workers.tasks.crawl import site_map_crawl

    try:
        site_map_crawl.delay(job_id, max_pages=max_pages, max_depth=max_depth)
        return "celery"
    except Exception as exc:
        logger.warning("Celery unavailable (%s) — running site map in background thread", exc)
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
