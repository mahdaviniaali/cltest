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


def celery_worker_available() -> bool:
    """True only when at least one Celery worker responds to inspect ping."""
    if not _broker_available(settings.CELERY_BROKER_URL):
        return False
    try:
        from app.workers.celery_app import celery_app

        ping = celery_app.control.inspect(timeout=1.0).ping()
        return bool(ping)
    except Exception as exc:
        logger.debug("Celery worker inspect failed: %s", exc)
        return False


def _dispatch_on_demand_thread(job_id: str) -> str:
    logger.info("Running on-demand job %s in background thread", job_id)
    thread = threading.Thread(
        target=_run_on_demand_in_thread,
        args=(job_id,),
        daemon=True,
        name=f"on-demand-{job_id[:8]}",
    )
    thread.start()
    return "thread"


def dispatch_site_map_job(
    job_id: str,
    *,
    max_pages: Optional[int] = None,
    max_depth: Optional[int] = None,
) -> str:
    """Enqueue site map via Celery when a worker is up; otherwise background thread.

    Broker-up is not enough: Redis from another project on :6379 would accept
    the publish and the job would sit unconsumed until API reload cancelled it.
    """
    if _broker_available(settings.CELERY_BROKER_URL) and celery_worker_available():
        from app.workers.tasks.crawl import site_map_crawl

        try:
            site_map_crawl.delay(job_id, max_pages=max_pages, max_depth=max_depth)
            return "celery"
        except Exception as exc:
            logger.warning("Celery publish failed (%s) — using background thread", exc)

    logger.info("No live Celery worker — running site map job %s in background thread", job_id)
    thread = threading.Thread(
        target=_run_site_map_in_thread,
        args=(job_id,),
        kwargs={"max_pages": max_pages, "max_depth": max_depth},
        daemon=True,
        name=f"site-map-{job_id[:8]}",
    )
    thread.start()
    return "thread"


def dispatch_on_demand_job(job_id: str) -> str:
    """Enqueue on-demand crawl via Celery when a worker is up; otherwise background thread."""
    if _broker_available(settings.CELERY_BROKER_URL) and celery_worker_available():
        from app.workers.tasks.crawl import on_demand_crawl

        try:
            on_demand_crawl.delay(job_id)
            return "celery"
        except Exception as exc:
            logger.warning("Celery publish failed (%s) — using background thread", exc)

    return _dispatch_on_demand_thread(job_id)


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


def _run_on_demand_in_thread(job_id: str) -> None:
    from app.db.engine import SessionLocal
    from crawler.application.crawl_job_runner import run_on_demand_job

    session = SessionLocal()
    try:
        run_on_demand_job(session, job_id)
    except Exception:
        logger.exception("Background on-demand job failed: %s", job_id)
    finally:
        session.close()
