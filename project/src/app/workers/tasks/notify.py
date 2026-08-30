from __future__ import annotations

import logging

from app.db.engine import SessionLocal
from app.services.notification import NotificationService
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="notify.send", bind=True, max_retries=3)
def send_notification(self, match_id: int) -> dict:
    session = SessionLocal()
    try:
        service = NotificationService(session)
        sent = service.send_for_match(match_id)
        session.commit()
        return {"match_id": match_id, "sent": sent}
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
