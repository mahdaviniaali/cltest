from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from config.bama_site import BamaSiteConfig
from crawler.domain.link_scorer import infer_page_role
from crawler.domain.page_classification import classify_url, detect_section
from crawler.domain.url_identity import canonicalize_url
from crawler.domain.url_patterns import infer_url_pattern, path_depth


@dataclass(slots=True)
class PageClassification:
    page_type: str
    section: str | None
    title: str | None
    excerpt: str | None
    url_pattern: str


class BamaPageClassifier:
    def __init__(self, config: BamaSiteConfig) -> None:
        self._config = config

    def classify(self, html: str, *, url: str) -> PageClassification:
        soup = BeautifulSoup(html, "lxml")
        title = self._extract_title(soup)
        excerpt = self._extract_excerpt(soup)
        has_query = bool(urlparse(url).query)
        canonical = canonicalize_url(url, self._config.canonical.strip_query_params) or url
        url_pattern = infer_url_pattern(canonical)
        section = detect_section(canonical, url_pattern, self._config, title=title)
        page_type = infer_page_role(
            canonical,
            self._config,
            inferred_pattern=url_pattern,
            has_query=has_query,
            path_depth=path_depth(canonical),
        )
        return PageClassification(
            page_type=page_type,
            section=section,
            title=title,
            excerpt=excerpt,
            url_pattern=url_pattern,
        )

    def classify_url_only(self, url: str) -> PageClassification:
        page_type, section, url_pattern = classify_url(url, self._config)
        return PageClassification(
            page_type=page_type,
            section=section,
            title=None,
            excerpt=None,
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
