from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass

from bs4 import BeautifulSoup

from config.bama_site import BamaSiteConfig, SectionHint
from crawler.domain.url_patterns import infer_url_pattern

DETAIL_PATTERNS = (
    re.compile(r"/car/detail-(?P<id>\d+)", re.I),
    re.compile(r"/motorcycle/detail-(?P<id>\d+)", re.I),
    re.compile(r"/truck/detail-(?P<id>\d+)", re.I),
)
LISTING_HINTS = ("page=", "/car", "/motorcycle", "/truck")
PAGINATION_RE = re.compile(r"[?&]page=\d+")


@dataclass(slots=True)
class PageClassification:
    page_type: str
    section: str | None
    title: str | None
    excerpt: str | None
    url_pattern: str


class BamaPageClassifier:
    def __init__(self, config: BamaSiteConfig) -> None:
        self._hints = config.section_hints

    def classify(self, html: str, *, url: str) -> PageClassification:
        soup = BeautifulSoup(html, "lxml")
        title = self._extract_title(soup)
        excerpt = self._extract_excerpt(soup)
        url_pattern = infer_url_pattern(url)
        section = self._detect_section(url, url_pattern, title)
        page_type = self._detect_page_type(url, url_pattern, soup)
        return PageClassification(
            page_type=page_type,
            section=section,
            title=title,
            excerpt=excerpt,
            url_pattern=url_pattern,
        )

    def _extract_title(self, soup: BeautifulSoup) -> str | None:
        og = soup.find("meta", property="og:title")
        if og and og.get("content"):
            return str(og["content"]).strip()
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
        title = soup.find("title")
        return title.get_text(strip=True) if title else None

    def _extract_excerpt(self, soup: BeautifulSoup) -> str | None:
        desc = soup.find("meta", attrs={"name": "description"})
        if desc and desc.get("content"):
            return str(desc["content"]).strip()[:320]
        og = soup.find("meta", property="og:description")
        if og and og.get("content"):
            return str(og["content"]).strip()[:320]
        return None

    def _detect_section(
        self,
        url: str,
        url_pattern: str,
        title: str | None,
    ) -> str | None:
        path = url.split("://", 1)[-1]
        path = path.split("/", 1)[-1]
        path = "/" + path.split("?", 1)[0]
        for hint in self._hints:
            if self._matches_hint(path, url_pattern, hint):
                return hint.section
        if title:
            lowered = title.lower()
            for hint in self._hints:
                if hint.section in lowered or hint.label in title:
                    return hint.section
        return None

    def _matches_hint(self, path: str, url_pattern: str, hint: SectionHint) -> bool:
        pat = hint.pattern
        if pat.startswith("/"):
            return fnmatch.fnmatch(path, pat) or fnmatch.fnmatch(url_pattern, f"*://*/*{pat.lstrip('/')}*")
        return fnmatch.fnmatch(path, pat) or fnmatch.fnmatch(url, pat)

    def _detect_page_type(self, url: str, url_pattern: str, soup: BeautifulSoup) -> str:
        for pattern in DETAIL_PATTERNS:
            if pattern.search(url):
                return "detail"
        if PAGINATION_RE.search(url) or any(h in url.lower() for h in LISTING_HINTS):
            cards = soup.find_all("a", href=True)
            detail_links = sum(
                1 for a in cards if any(p.search(a["href"]) for p in DETAIL_PATTERNS)
            )
            if detail_links >= 3:
                return "listing"
        segments = [s for s in url.split("/") if s and "?" not in s][3:]
        if len(segments) <= 1:
            return "hub"
        if "{id}" in url_pattern or "detail" in url_pattern:
            return "detail"
        return "static"
