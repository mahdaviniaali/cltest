from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from config.bama_site import BamaSiteConfig, SectionHint
from crawler.domain.link_scorer import infer_page_role
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
        self._hints = config.section_hints

    def classify(self, html: str, *, url: str) -> PageClassification:
        soup = BeautifulSoup(html, "lxml")
        title = self._extract_title(soup)
        excerpt = self._extract_excerpt(soup)
        canonical = canonicalize_url(url, self._config.canonical.strip_query_params) or url
        url_pattern = infer_url_pattern(canonical)
        parsed = urlparse(canonical)
        has_query = bool(parsed.query)
        section = self._detect_section(canonical, url_pattern, title)
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
        for root in self._config.section_roots:
            root_path = root.url.split("://", 1)[-1].rstrip("/")
            path = url.split("://", 1)[-1].split("?", 1)[0].rstrip("/")
            if path == root_path or path.startswith(root_path + "/"):
                return root.section

        path = url.split("://", 1)[-1]
        path = path.split("/", 1)[-1]
        path = "/" + path.split("?", 1)[0]
        for hint in self._hints:
            if self._matches_hint(path, url_pattern, hint):
                return hint.section
        if title:
            for hint in self._hints:
                if hint.section in title.lower() or hint.label in title:
                    return hint.section
        return None

    def _matches_hint(self, path: str, url_pattern: str, hint: SectionHint) -> bool:
        pat = hint.pattern
        if pat.startswith("/"):
            return fnmatch.fnmatch(path, pat) or fnmatch.fnmatch(
                url_pattern, f"*://*/*{pat.lstrip('/')}*"
            )
        return fnmatch.fnmatch(path, pat) or fnmatch.fnmatch(url, pat)
