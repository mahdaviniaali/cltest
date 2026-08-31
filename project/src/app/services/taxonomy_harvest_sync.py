from __future__ import annotations

import logging
import threading
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.repositories.taxonomy_repository import TaxonomyRepository
from crawler.application.taxonomy_harvest import TaxonomyHarvestService

logger = logging.getLogger(__name__)

_harvest_lock = threading.Lock()


def ensure_taxonomy_catalog(session: Session) -> Optional[dict[str, Any]]:
    """Populate brand/model catalog from Bama sitemaps when empty."""
    repo = TaxonomyRepository(session)
    if repo.count_active_terms(term_type="brand") > 0:
        return None
    with _harvest_lock:
        if repo.count_active_terms(term_type="brand") > 0:
            return None
        try:
            summary = TaxonomyHarvestService(session).harvest(job_id="taxonomy-ensure")
            session.commit()
            return summary
        except Exception:
            logger.exception("Taxonomy harvest failed")
            session.rollback()
            return None


def refresh_taxonomy_catalog(session: Session, *, job_id: str | None = None) -> dict[str, Any]:
    with _harvest_lock:
        return TaxonomyHarvestService(session).harvest(job_id=job_id or "taxonomy-refresh")
