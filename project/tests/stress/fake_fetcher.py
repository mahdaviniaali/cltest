"""In-memory fetcher backed by pre-built HTML maps."""

from __future__ import annotations

from typing import Optional


class VolumeFakeFetcher:
    def __init__(
        self,
        pages: dict[str, str],
        details: dict[str, str],
    ) -> None:
        self._pages = pages
        self._details = details
        self.calls: list[str] = []

    def fetch(self, url: str) -> Optional[str]:
        self.calls.append(url)
        if url in self._pages:
            return self._pages[url]
        if url in self._details:
            return self._details[url]
        return None
