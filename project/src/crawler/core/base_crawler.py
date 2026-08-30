import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Iterable, List, Optional

from .http_client import HttpClient

logger = logging.getLogger(__name__)


class BaseCrawler(ABC):
    """Abstract base class for web crawlers."""

    def __init__(
        self,
        http_client: HttpClient,
        delay: float = 1.0,
    ) -> None:
        self.http_client = http_client
        self.delay = delay
        self.results: List[Any] = []

    def crawl(self, urls: Iterable[str]) -> List[Any]:
        """Fetch and parse a list of URLs."""
        self.results = []

        for url in urls:
            logger.info("Crawling: %s", url)
            response = self.http_client.get(url)

            if response is not None:
                parsed = self.parse(url, response.text)
                if parsed is not None:
                    self.results.append(parsed)

            time.sleep(self.delay)

        return self.results

    @abstractmethod
    def parse(self, url: str, html: str) -> Optional[Any]:
        """Parse raw HTML and return structured data."""
