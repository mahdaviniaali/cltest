from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

from crawler.domain.url_identity import is_asset_url, normalize_url, same_domain

SITEMAP_LOC = re.compile(r"<loc>\s*([^<]+)\s*</loc>", re.I)


@dataclass(slots=True)
class CrawlPolicy:
    policy_id: str = "default"
    max_depth: int = 8
    max_pages: int = 5000
    allow_domains: list[str] = field(default_factory=list)
    deny_domains: list[str] = field(default_factory=list)
    include_patterns: list[str] = field(default_factory=list)
    exclude_patterns: list[str] = field(default_factory=list)
    respect_robots: bool = True


def domain_allowed(url: str, policy: CrawlPolicy, *, seed: str) -> bool:
    host = urlparse(url).netloc.lower()
    if policy.deny_domains and any(host == d or host.endswith("." + d) for d in policy.deny_domains):
        return False
    if policy.allow_domains:
        return any(host == d or host.endswith("." + d) for d in policy.allow_domains)
    return same_domain(url, seed)


def pattern_allowed(url: str, policy: CrawlPolicy) -> bool:
    path = urlparse(url).path or "/"
    for pat in policy.exclude_patterns:
        if fnmatch.fnmatch(path, pat) or fnmatch.fnmatch(url, pat):
            return False
    if not policy.include_patterns:
        return True
    return any(fnmatch.fnmatch(path, pat) or fnmatch.fnmatch(url, pat) for pat in policy.include_patterns)


def url_in_scope(url: str, policy: CrawlPolicy, *, seed: str) -> bool:
    normalized = normalize_url(url)
    if not normalized:
        return False
    if is_asset_url(normalized):
        return False
    if not domain_allowed(normalized, policy, seed=seed):
        return False
    return pattern_allowed(normalized, policy)


def parse_sitemap_locs(xml_text: str) -> list[str]:
    return [m.group(1).strip() for m in SITEMAP_LOC.finditer(xml_text)]
