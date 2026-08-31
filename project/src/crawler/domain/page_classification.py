from __future__ import annotations

from urllib.parse import urlparse

from config.bama_site import BamaSiteConfig, SectionHint
from crawler.domain.link_scorer import infer_page_role
from crawler.domain.url_identity import canonicalize_url
from crawler.domain.url_patterns import infer_url_pattern, path_depth


def detect_section(
    url: str,
    url_pattern: str,
    config: BamaSiteConfig,
    *,
    title: str | None = None,
) -> str | None:
    for root in config.section_roots:
        root_path = root.url.split("://", 1)[-1].rstrip("/")
        path = url.split("://", 1)[-1].split("?", 1)[0].rstrip("/")
        if path == root_path or path.startswith(root_path + "/"):
            return root.section

    path = url.split("://", 1)[-1]
    path = path.split("/", 1)[-1]
    path = "/" + path.split("?", 1)[0]
    for hint in config.section_hints:
        if _matches_hint(path, url_pattern, hint):
            return hint.section
    if title:
        for hint in config.section_hints:
            if hint.section in title.lower() or hint.label in title:
                return hint.section
    return None


def classify_url(url: str, config: BamaSiteConfig) -> tuple[str, str | None, str]:
    """URL-only classification (no HTML)."""
    return classify_node(url, config)


def classify_node(
    url: str,
    config: BamaSiteConfig,
    *,
    title: str | None = None,
) -> tuple[str, str | None, str]:
    """Classify from URL; optional title improves section detection on crawled pages."""
    has_query = bool(urlparse(url).query)
    canonical = canonicalize_url(url, config.canonical.strip_query_params) or url
    url_pattern = infer_url_pattern(canonical)
    section = detect_section(canonical, url_pattern, config, title=title)
    page_type = infer_page_role(
        canonical,
        config,
        inferred_pattern=url_pattern,
        has_query=has_query,
        path_depth=path_depth(canonical),
    )
    return page_type, section, url_pattern


def _matches_hint(path: str, url_pattern: str, hint: SectionHint) -> bool:
    import fnmatch

    pat = hint.pattern
    if pat.startswith("/"):
        return fnmatch.fnmatch(path, pat) or fnmatch.fnmatch(
            url_pattern, f"*://*/*{pat.lstrip('/')}*"
        )
    return fnmatch.fnmatch(path, pat) or fnmatch.fnmatch(url, pat)
