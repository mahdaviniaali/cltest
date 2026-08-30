from __future__ import annotations

import logging
from typing import Optional

from crawler.domain.ports import PageFetcher

logger = logging.getLogger(__name__)


class Crawl4AiPageFetcher(PageFetcher):
    """Optional JS-rendered fetcher — crawl4ai imported only here (ADR-004)."""

    def __init__(self, *, user_agent: str, timeout: float = 30.0) -> None:
        self._user_agent = user_agent
        self._timeout = timeout

    def fetch(self, url: str) -> Optional[str]:
        try:
            from crawl4ai import AsyncWebCrawler
            import asyncio
        except ImportError:
            logger.warning("crawl4ai not installed — skipping JS fetch for %s", url)
            return None

        async def _run() -> Optional[str]:
            async with AsyncWebCrawler(verbose=False) as crawler:
                result = await crawler.arun(
                    url=url,
                    headers={"User-Agent": self._user_agent},
                )
                if result.success:
                    return result.html
                return None

        try:
            return asyncio.run(_run())
        except Exception as exc:
            logger.warning("Crawl4AI fetch failed for %s: %s", url, exc)
            return None
