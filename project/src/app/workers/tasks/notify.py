from __future__ import annotations

import logging

from app.db.engine import SessionLocal
from app.services.notification_orchestrator import NotificationOrchestrator
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="notify.orchestrate", bind=True, max_retries=3)
def orchestrate_notification(self, match_id: int) -> dict:
    session = SessionLocal()
    try:
        service = NotificationOrchestrator(session)
        result = service.orchestrate(match_id)
        session.commit()
        return result
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@celery_app.task(name="notify.send", bind=True, max_retries=3)
def send_notification(self, match_id: int) -> dict:
    """Deprecated alias — use notify.orchestrate."""
    return orchestrate_notification(match_id)
