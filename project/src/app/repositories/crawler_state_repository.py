from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.crawler_state import CrawlerState

DEFAULT_SOURCE_KEY = "bama:car:listings"


class CrawlerStateRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, source_key: str = DEFAULT_SOURCE_KEY) -> Optional[CrawlerState]:
        return self._session.get(CrawlerState, source_key)

    def get_or_create(self, source_key: str = DEFAULT_SOURCE_KEY) -> CrawlerState:
        state = self.get(source_key)
        if state is None:
            state = CrawlerState(source_key=source_key)
            self._session.add(state)
            self._session.flush()
        return state

    def update_checkpoint(
        self,
        *,
        last_seen_bama_id: str,
        job_id: str,
        source_key: str = DEFAULT_SOURCE_KEY,
    ) -> CrawlerState:
        state = self.get_or_create(source_key)
        state.last_seen_bama_id = last_seen_bama_id
        state.last_crawl_at = datetime.now(timezone.utc)
        state.last_run_job_id = job_id
        self._session.flush()
        return state
