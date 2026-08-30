from typing import Any, Dict, Optional

from crawler.core.base_crawler import BaseCrawler
from crawler.parsers.html_parser import HtmlParser


class ExampleCrawler(BaseCrawler):
    """Sample crawler that extracts page title and meta tags."""

    def parse(self, url: str, html: str) -> Optional[Dict[str, Any]]:
        title = HtmlParser.extract_title(html)
        meta = HtmlParser.extract_meta(html)

        if not title and not meta:
            return None

        return {
            "url": url,
            "title": title,
            "meta": meta,
        }
