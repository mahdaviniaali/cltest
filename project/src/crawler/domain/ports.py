from __future__ import annotations

from typing import Optional, Protocol

from crawler.domain.entities import AdDraft, ListingCard


class PageFetcher(Protocol):
    def fetch(self, url: str) -> Optional[str]:
        """Return HTML body or None on failure."""


class ListingParser(Protocol):
    def parse(self, html: str, *, page: int) -> list[ListingCard]:
        ...

    def next_page_url(self, current_url: str, page: int) -> str:
        ...


class DetailParser(Protocol):
    def parse(self, html: str, *, url: str, bama_id: str) -> AdDraft:
        ...


class AdStore(Protocol):
    def save_new(self, draft: AdDraft) -> tuple[int, bool]:
        """Returns (ad_id, created). Writes outbox on create in same transaction."""


class CrawlCheckpointStore(Protocol):
    def get_last_seen_bama_id(self) -> Optional[str]:
        ...

    def update_checkpoint(self, bama_id: str, job_id: str) -> None:
        ...
