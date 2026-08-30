from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from crawler.domain.crawl_policy import CrawlPolicy

_CONFIG_PATH = Path(__file__).resolve().parent / "bama_site.yaml"


@dataclass(slots=True)
class SectionHint:
    pattern: str
    section: str
    label: str = ""


@dataclass(slots=True)
class SectionRoot:
    url: str
    section: str
    weight: int = 10


@dataclass(slots=True)
class RouteRule:
    pattern: str
    role: str
    weight: int = 1
    priority: int = 0

    def matches_url(self, url: str, inferred_pattern: str) -> bool:
        from crawler.domain.link_scorer import match_route_pattern

        return match_route_pattern(url, inferred_pattern, self.pattern)


@dataclass(slots=True)
class CanonicalConfig:
    strip_query_params: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RoleDefaults:
    has_query: str = "listing"
    path_depth_lte_1: str = "section_hub"
    fallback: str = "unknown"


@dataclass(slots=True)
class BamaSiteConfig:
    seed_urls: list[str] = field(default_factory=lambda: ["https://bama.ir/"])
    domain_allow: list[str] = field(default_factory=lambda: ["bama.ir"])
    exclude_patterns: list[str] = field(default_factory=list)
    section_hints: list[SectionHint] = field(default_factory=list)
    section_roots: list[SectionRoot] = field(default_factory=list)
    route_rules: list[RouteRule] = field(default_factory=list)
    canonical: CanonicalConfig = field(default_factory=CanonicalConfig)
    role_defaults: RoleDefaults = field(default_factory=RoleDefaults)
    sitemap_max_urls: int = 20
    sitemap_defer: bool = True
    default_max_depth: int = 6
    default_max_pages: int = 5000

    def to_crawl_policy(self) -> CrawlPolicy:
        return CrawlPolicy(
            policy_id="bama",
            max_depth=self.default_max_depth,
            max_pages=self.default_max_pages,
            allow_domains=list(self.domain_allow),
            exclude_patterns=list(self.exclude_patterns),
            respect_robots=True,
        )

    def section_weight_for_url(self, url: str) -> int:
        path = url.split("://", 1)[-1].split("?", 1)[0]
        for root in self.section_roots:
            root_path = root.url.split("://", 1)[-1].rstrip("/")
            if path.rstrip("/") == root_path or path.startswith(root_path + "/"):
                return root.weight
        return 1

    def match_route_rule(self, url: str, inferred_pattern: str) -> RouteRule | None:
        for rule in sorted(self.route_rules, key=lambda r: -r.priority):
            if rule.matches_url(url, inferred_pattern):
                return rule
        return None


def load_bama_site_config(path: Path | None = None) -> BamaSiteConfig:
    cfg_path = path or _CONFIG_PATH
    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    hints = [
        SectionHint(
            pattern=str(item["pattern"]),
            section=str(item["section"]),
            label=str(item.get("label") or item["section"]),
        )
        for item in raw.get("section_hints") or []
    ]
    roots = [
        SectionRoot(
            url=str(item["url"]),
            section=str(item["section"]),
            weight=int(item.get("weight") or 10),
        )
        for item in raw.get("section_roots") or []
    ]
    rules = [
        RouteRule(
            pattern=str(item["pattern"]),
            role=str(item["role"]),
            weight=int(item.get("weight") or 1),
            priority=int(item.get("priority") or 0),
        )
        for item in raw.get("route_rules") or []
    ]
    canon_raw = raw.get("canonical") or {}
    canonical = CanonicalConfig(
        strip_query_params=list(canon_raw.get("strip_query_params") or []),
    )
    defaults_raw = raw.get("default_role_defaults") or {}
    role_defaults = RoleDefaults(
        has_query=str(defaults_raw.get("has_query") or "listing"),
        path_depth_lte_1=str(defaults_raw.get("path_depth_lte_1") or "section_hub"),
        fallback=str(defaults_raw.get("fallback") or "unknown"),
    )
    return BamaSiteConfig(
        seed_urls=list(raw.get("seed_urls") or ["https://bama.ir/"]),
        domain_allow=list(raw.get("domain_allow") or ["bama.ir"]),
        exclude_patterns=list(raw.get("exclude_patterns") or []),
        section_hints=hints,
        section_roots=roots,
        route_rules=rules,
        canonical=canonical,
        role_defaults=role_defaults,
        sitemap_max_urls=int(raw.get("sitemap_max_urls") or 20),
        sitemap_defer=bool(raw.get("sitemap_defer", True)),
        default_max_depth=int(raw.get("default_max_depth") or 6),
        default_max_pages=int(raw.get("default_max_pages") or 5000),
    )
