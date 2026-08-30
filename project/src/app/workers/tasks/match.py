from __future__ import annotations

import logging

from app.db.engine import SessionLocal
from app.services.matching import MatchingService
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="match.process_ad", bind=True, max_retries=3)
def process_ad(self, ad_id: int) -> dict:
    session = SessionLocal()
    try:
        service = MatchingService(session)
        matches = service.process_new_ad(ad_id)
        session.commit()
        return {"ad_id": ad_id, "matches": len(matches)}
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
