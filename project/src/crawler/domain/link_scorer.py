from __future__ import annotations

import fnmatch
from urllib.parse import urlparse

from config.bama_site import BamaSiteConfig


def match_route_pattern(url: str, inferred_pattern: str, rule_pattern: str) -> bool:
    """Match URL or inferred template against a config route rule pattern."""
    if rule_pattern == inferred_pattern:
        return True
    if rule_pattern.rstrip("/") == url.rstrip("/"):
        return True

    url_path = urlparse(url).path.rstrip("/") or "/"
    rule_path = urlparse(rule_pattern).path.rstrip("/") or "/"
    inf_path = urlparse(inferred_pattern).path.rstrip("/") or "/"

    if "*" in rule_pattern:
        candidates = (
            inferred_pattern,
            inf_path,
            url,
            url_path,
        )
        for candidate in candidates:
            if fnmatch.fnmatch(candidate, rule_pattern):
                return True
            if fnmatch.fnmatch(candidate, rule_pattern.replace("://", "://*")):
                return True
        rule_glob = _rule_to_glob(rule_pattern)
        return fnmatch.fnmatch(inferred_pattern, rule_glob) or fnmatch.fnmatch(inf_path, rule_glob)

    return _template_match(inf_path, rule_path) or _template_match(url_path, rule_path)


def _rule_to_glob(rule_pattern: str) -> str:
    parsed = urlparse(rule_pattern)
    segments = [s for s in parsed.path.split("/") if s]
    glob_segments: list[str] = []
    for segment in segments:
        if segment == "*":
            glob_segments.append("*")
        elif segment.startswith("{") and segment.endswith("}"):
            glob_segments.append("*")
        else:
            glob_segments.append(segment)
    path = "/" + "/".join(glob_segments) if glob_segments else "/*"
    return f"{parsed.scheme}://{parsed.netloc}{path}"


def _template_match(path: str, rule_path: str) -> bool:
    path_segments = [s for s in path.split("/") if s]
    rule_segments = [s for s in rule_path.split("/") if s]
    if len(path_segments) != len(rule_segments):
        return False
    for path_seg, rule_seg in zip(path_segments, rule_segments, strict=False):
        if rule_seg.startswith("{") and rule_seg.endswith("}"):
            continue
        if path_seg.lower() != rule_seg.lower():
            return False
    return True


def score_url(url: str, config: BamaSiteConfig, *, inferred_pattern: str | None = None) -> int:
    """Highest-priority matching route_rule weight wins; else section_roots prefix weight."""
    from crawler.domain.url_patterns import infer_url_pattern

    pattern = inferred_pattern or infer_url_pattern(url)
    rule = config.match_route_rule(url, pattern)
    if rule is not None:
        return rule.weight
    return config.section_weight_for_url(url)


def infer_page_role(
    url: str,
    config: BamaSiteConfig,
    *,
    inferred_pattern: str | None = None,
    has_query: bool = False,
    path_depth: int | None = None,
) -> str:
    from crawler.domain.url_patterns import infer_url_pattern, path_depth as compute_path_depth

    pattern = inferred_pattern or infer_url_pattern(url)
    if has_query:
        return config.role_defaults.has_query
    rule = config.match_route_rule(url, pattern)
    if rule is not None:
        return rule.role
    depth = path_depth if path_depth is not None else compute_path_depth(url)
    if depth <= 1:
        return config.role_defaults.path_depth_lte_1
    return config.role_defaults.fallback
