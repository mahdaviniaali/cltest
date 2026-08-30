from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from crawler.domain.url_identity import normalize_url


@dataclass(slots=True)
class ExtractedLink:
    url: str
    text: str


class LinkExtractor:
    def extract(self, html: str, *, base_url: str) -> list[ExtractedLink]:
        soup = BeautifulSoup(html, "lxml")
        canonical = soup.find("link", rel="canonical")
        links: list[ExtractedLink] = []
        seen: set[str] = set()

        if canonical and canonical.get("href"):
            norm = normalize_url(canonical["href"], base_url)
            if norm and norm not in seen:
                seen.add(norm)
                links.append(ExtractedLink(url=norm, text="canonical"))

        for anchor in soup.find_all("a", href=True):
            href = anchor.get("href", "").strip()
            if not href or href.startswith("#"):
                continue
            norm = normalize_url(href, base_url)
            if not norm or norm in seen:
                continue
            seen.add(norm)
            text = anchor.get_text(" ", strip=True)[:200]
            links.append(ExtractedLink(url=norm, text=text))

        return links
