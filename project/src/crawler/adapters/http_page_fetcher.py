from __future__ import annotations

import logging
import time
from typing import Optional
from urllib.parse import urlparse

from crawler.core.http_client import HttpClient
from crawler.domain.ports import PageFetcher

logger = logging.getLogger(__name__)


def robots_allowed(url: str, robots_text: str, user_agent: str) -> bool:
    from urllib.robotparser import RobotFileParser

    parser = RobotFileParser()
    parser.parse(robots_text.splitlines())
    return parser.can_fetch(user_agent, url)


def robots_url_for(page_url: str) -> str:
    parsed = urlparse(page_url)
    return f"{parsed.scheme}://{parsed.netloc}/robots.txt"


class HttpPageFetcher(PageFetcher):
    def __init__(
        self,
        http_client: HttpClient,
        *,
        user_agent: str,
        respect_robots: bool = True,
    ) -> None:
        self._http = http_client
        self._user_agent = user_agent
        self._respect_robots = respect_robots
        self._robots_cache: dict[str, Optional[str]] = {}

    def fetch(self, url: str) -> Optional[str]:
        if self._respect_robots and not self._check_robots(url):
            logger.warning("Robots disallowed: %s", url)
            return None
        response = self._http.get(url)
        if response is None:
            return None
        return response.text

    def _check_robots(self, url: str) -> bool:
        r_url = robots_url_for(url)
        if r_url not in self._robots_cache:
            response = self._http.get(r_url)
            self._robots_cache[r_url] = response.text if response is not None else None
        robots_text = self._robots_cache[r_url]
        if robots_text is None:
            return True
        return robots_allowed(url, robots_text, self._user_agent)


class DelayedPageFetcher(PageFetcher):
    """Decorator adding delay between fetches."""

    def __init__(self, inner: PageFetcher, delay_seconds: float) -> None:
        self._inner = inner
        self._delay = delay_seconds

    def fetch(self, url: str) -> Optional[str]:
        html = self._inner.fetch(url)
        if self._delay > 0:
            time.sleep(self._delay)
        return html
