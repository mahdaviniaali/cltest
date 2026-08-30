from __future__ import annotations

import logging

from app.db.engine import SessionLocal
from app.services.outbox_relay import OutboxRelayService
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="outbox.relay")
def relay_outbox(batch_size: int = 50) -> dict:
    session = SessionLocal()
    try:
        service = OutboxRelayService(session)
        processed = service.relay(batch_size=batch_size)
        session.commit()
        return {"processed": processed}
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
