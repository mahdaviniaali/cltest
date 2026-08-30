from __future__ import annotations

from collections import defaultdict

from sqlalchemy.orm import Session

from app.models.site_map import SiteNode
from app.repositories.site_node_repository import SiteNodeRepository
from app.repositories.site_section_repository import SiteSectionRepository
from config.bama_site import BamaSiteConfig


class SiteCatalogBuilder:
    def __init__(
        self,
        session: Session,
        config: BamaSiteConfig,
    ) -> None:
        self._session = session
        self._config = config
        self._nodes = SiteNodeRepository(session)
        self._sections = SiteSectionRepository(session)

    def build(self) -> list[dict]:
        nodes = self._nodes.list_all(limit=100_000)
        by_section: dict[str, list[SiteNode]] = defaultdict(list)
        for node in nodes:
            key = node.section or "unknown"
            by_section[key].append(node)

        self._sections.clear_all()
        results: list[dict] = []
        hint_labels = {h.section: h.label for h in self._config.section_hints}

        for section_key, section_nodes in by_section.items():
            patterns: dict[str, int] = defaultdict(int)
            roots: set[str] = set()
            for node in section_nodes:
                patterns[node.url_pattern] += 1
                if node.depth <= 1:
                    roots.add(node.url)
            useful = self._score_section(section_nodes)
            label = hint_labels.get(section_key, section_key)
            pattern_list = sorted(patterns.keys(), key=lambda p: patterns[p], reverse=True)
            self._sections.upsert(
                section_key=section_key,
                label=label,
                root_urls=sorted(roots)[:20],
                url_patterns=pattern_list[:50],
                page_count=len(section_nodes),
                useful_score=useful,
            )
            results.append(
                {
                    "section_key": section_key,
                    "label": label,
                    "page_count": len(section_nodes),
                    "useful_score": useful,
                    "url_patterns": pattern_list[:10],
                }
            )

        self._session.flush()
        return sorted(results, key=lambda r: r["useful_score"], reverse=True)

    def _score_section(self, nodes: list[SiteNode]) -> float:
        score = 0.0
        for node in nodes:
            if node.page_type == "listing":
                score += 3.0
            elif node.page_type == "detail":
                score += 5.0
            elif node.page_type == "hub":
                score += 1.0
            else:
                score += 0.2
        return round(score, 2)
