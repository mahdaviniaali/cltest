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
class BamaSiteConfig:
    seed_urls: list[str] = field(default_factory=lambda: ["https://bama.ir/"])
    domain_allow: list[str] = field(default_factory=lambda: ["bama.ir"])
    exclude_patterns: list[str] = field(default_factory=list)
    section_hints: list[SectionHint] = field(default_factory=list)
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
    return BamaSiteConfig(
        seed_urls=list(raw.get("seed_urls") or ["https://bama.ir/"]),
        domain_allow=list(raw.get("domain_allow") or ["bama.ir"]),
        exclude_patterns=list(raw.get("exclude_patterns") or []),
        section_hints=hints,
        default_max_depth=int(raw.get("default_max_depth") or 6),
        default_max_pages=int(raw.get("default_max_pages") or 5000),
    )
