from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup


class HtmlParser:
    """Generic HTML parser utilities."""

    @staticmethod
    def extract_title(html: str) -> Optional[str]:
        soup = BeautifulSoup(html, "lxml")
        tag = soup.find("title")
        return tag.get_text(strip=True) if tag else None

    @staticmethod
    def extract_links(html: str, base_url: str = "") -> List[str]:
        soup = BeautifulSoup(html, "lxml")
        links: List[str] = []

        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            if href.startswith("http") or not base_url:
                links.append(href)
            else:
                links.append(base_url.rstrip("/") + "/" + href.lstrip("/"))

        return links

    @staticmethod
    def extract_meta(html: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html, "lxml")
        meta: Dict[str, Any] = {}

        for tag in soup.find_all("meta"):
            name = tag.get("name") or tag.get("property")
            content = tag.get("content")
            if name and content:
                meta[name] = content

        return meta
