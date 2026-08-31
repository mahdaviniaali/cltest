from __future__ import annotations

from collections import defaultdict
from urllib.parse import urlparse

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.site_map import SiteEdge, SiteMapGroupKind, SiteNode
from app.repositories.site_map_group_repository import SiteMapGroupRepository
from app.repositories.site_node_repository import SiteNodeRepository
from app.repositories.site_section_repository import SiteSectionRepository
from config.bama_site import BamaSiteConfig

ROOT_GROUP_KEY = "root:bama.ir"
PATH_HUB_DEPTH = 2
MIN_HUB_INBOUND = 5

_HUB_PAGE_TYPES = frozenset({"section_hub", "brand_hub", "model_hub", "hub"})
_SECTION_PATTERN_TYPES = frozenset({"ad_detail", "detail", "listing"})
_TYPE_LABELS = {
    "ad_detail": "آگهی",
    "detail": "آگهی",
    "listing": "لیست",
    "model_hub": "مدل",
    "section_hub": "بخش",
    "brand_hub": "برند",
    "hub": "هاب",
    "static": "ثابت",
    "unknown": "سایر",
}


class SiteMapProjectionBuilder:
    def __init__(
        self,
        session: Session,
        config: BamaSiteConfig,
    ) -> None:
        self._session = session
        self._config = config
        self._nodes = SiteNodeRepository(session)
        self._sections = SiteSectionRepository(session)
        self._groups = SiteMapGroupRepository(session)
        self._inbound_by_key = self._load_inbound_counts()

    def build(self) -> list[dict]:
        nodes = self._nodes.list_all(limit=100_000)
        sections = self._sections.list_all()
        self._groups.clear_all()

        by_section: dict[str, list[SiteNode]] = defaultdict(list)
        for node in nodes:
            by_section[node.section or "unknown"].append(node)

        root_nodes = [n for n in nodes if n.depth <= 1]
        root_rep = self._pick_representative(root_nodes or nodes)
        root_weight = self._node_weight(root_rep) if root_rep else 1
        self._upsert(
            group_key=ROOT_GROUP_KEY,
            parent_group_key=None,
            group_kind=SiteMapGroupKind.ROOT.value,
            label="bama.ir",
            section=None,
            path_prefix="/",
            url_pattern=None,
            page_type=root_rep.page_type if root_rep else "section_hub",
            page_count=len(nodes),
            weight=root_weight,
            inbound_link_count=0,
            representative=root_rep,
            depth=0,
            sort_order=self._sort_key(root_weight, len(nodes)),
        )

        section_rows = sections or [
            type("S", (), {"section_key": k, "label": k, "page_count": len(v)})()
            for k, v in by_section.items()
        ]

        for section in section_rows:
            section_key = section.section_key
            section_nodes = by_section.get(section_key, [])
            if not section_nodes:
                continue
            self._build_section(section_key, getattr(section, "label", section_key), section_nodes)

        self._session.flush()
        all_groups = self._groups.list_all()
        return [
            {
                "group_key": g.group_key,
                "group_kind": g.group_kind,
                "page_count": g.page_count,
            }
            for g in all_groups
        ]

    def _build_section(self, section_key: str, section_label: str, section_nodes: list[SiteNode]) -> None:
        section_rep = self._pick_representative(section_nodes)
        section_weight = self._node_weight(section_rep) if section_rep else 1
        section_group_key = f"section:{section_key}"
        self._upsert(
            group_key=section_group_key,
            parent_group_key=ROOT_GROUP_KEY,
            group_kind=SiteMapGroupKind.SECTION.value,
            label=section_label,
            section=section_key,
            path_prefix=f"/{section_key}" if section_key != "unknown" else None,
            url_pattern=None,
            page_type=section_rep.page_type if section_rep else None,
            page_count=len(section_nodes),
            weight=section_weight,
            inbound_link_count=self._group_inbound(section_nodes),
            representative=section_rep,
            depth=1,
            sort_order=self._sort_key(section_weight, len(section_nodes)),
        )

        pattern_nodes: list[SiteNode] = []
        hub_nodes: list[SiteNode] = []
        for node in section_nodes:
            if self._is_section_pattern_node(node):
                pattern_nodes.append(node)
            elif node.page_type in _HUB_PAGE_TYPES:
                hub_nodes.append(node)
            else:
                pattern_nodes.append(node)

        by_pattern: dict[str, list[SiteNode]] = defaultdict(list)
        for node in pattern_nodes:
            by_pattern[self._section_pattern_key(node, section_key)].append(node)

        merged_patterns: list[tuple[str, list[SiteNode], str]] = []
        singleton_nodes: list[SiteNode] = []
        for pattern_key, nodes in by_pattern.items():
            if pattern_key.startswith("listing:"):
                merged_patterns.append((pattern_key, nodes, self._listing_label(section_key)))
                continue
            if len(nodes) >= 2 or self._is_primary_pattern(pattern_key, nodes):
                merged_patterns.append((pattern_key, nodes, self._pattern_label(pattern_key, self._dominant_page_type(nodes))))
                continue
            singleton_nodes.extend(nodes)

        if singleton_nodes:
            merged_patterns.append(
                (
                    f"other:{section_key}",
                    singleton_nodes,
                    f"سایر صفحات ({len(singleton_nodes)})",
                )
            )

        for pattern_key, nodes, label in sorted(
            merged_patterns, key=lambda item: len(item[1]), reverse=True
        ):
            rep = self._pick_representative(nodes)
            page_type = self._dominant_page_type(nodes)
            pattern_group_key = f"pattern:{section_key}|{self._safe_key(pattern_key)}"
            display_pattern = pattern_key
            if pattern_key.startswith("listing:"):
                display_pattern = f"https://bama.ir/{section_key}/{{brand}}"
            elif pattern_key.startswith("other:"):
                display_pattern = rep.url_pattern if rep else None
            elif "://" not in pattern_key:
                display_pattern = rep.url_pattern if rep else None
            else:
                display_pattern = pattern_key
            self._upsert(
                group_key=pattern_group_key,
                parent_group_key=section_group_key,
                group_kind=SiteMapGroupKind.PATTERN_CLUSTER.value,
                label=label,
                section=section_key,
                path_prefix=urlparse(display_pattern).path if "://" in display_pattern else None,
                url_pattern=display_pattern if "://" in display_pattern else None,
                page_type=page_type,
                page_count=len(nodes),
                weight=self._node_weight(rep) if rep else 1,
                inbound_link_count=self._group_inbound(nodes),
                representative=rep,
                depth=2,
                sort_order=self._sort_key(self._node_weight(rep) if rep else 1, len(nodes)),
            )

        featured_hubs: list[SiteNode] = []
        minor_hubs: list[SiteNode] = []
        for node in hub_nodes:
            inbound = self._inbound_by_key.get(node.page_key, 0)
            if node.page_type == "section_hub" or inbound >= MIN_HUB_INBOUND:
                featured_hubs.append(node)
            else:
                minor_hubs.append(node)

        by_prefix: dict[str, list[SiteNode]] = defaultdict(list)
        for node in featured_hubs:
            by_prefix[self._path_prefix(node)].append(node)

        for prefix in sorted(by_prefix.keys(), key=lambda p: self._prefix_sort_key(by_prefix[p]), reverse=True):
            prefix_nodes = by_prefix[prefix]
            rep = self._pick_representative(prefix_nodes)
            inbound = self._group_inbound(prefix_nodes)
            safe_prefix = prefix.strip("/").replace("/", "_") or "home"
            path_group_key = f"path:{section_key}|{safe_prefix}"
            self._upsert(
                group_key=path_group_key,
                parent_group_key=section_group_key,
                group_kind=SiteMapGroupKind.PATH_HUB.value,
                label=self._path_label(prefix, rep),
                section=section_key,
                path_prefix=prefix,
                url_pattern=rep.url_pattern if rep else None,
                page_type=rep.page_type if rep else None,
                page_count=len(prefix_nodes),
                weight=self._node_weight(rep) if rep else 1,
                inbound_link_count=inbound,
                representative=rep,
                depth=2,
                sort_order=self._sort_key(self._node_weight(rep) if rep else 1, len(prefix_nodes), inbound),
            )

        if minor_hubs:
            rep = self._pick_representative(minor_hubs)
            generic_pattern = f"https://bama.ir/{section_key}/{{brand}}"
            if section_key == "unknown":
                generic_pattern = "https://bama.ir/{path}"
            self._upsert(
                group_key=f"path:{section_key}|other_hubs",
                parent_group_key=section_group_key,
                group_kind=SiteMapGroupKind.PATH_HUB.value,
                label=f"سایر هاب‌ها ({len(minor_hubs)})",
                section=section_key,
                path_prefix=f"/{section_key}" if section_key != "unknown" else None,
                url_pattern=generic_pattern,
                page_type="model_hub",
                page_count=len(minor_hubs),
                weight=5,
                inbound_link_count=self._group_inbound(minor_hubs),
                representative=rep,
                depth=2,
                sort_order=self._sort_key(5, len(minor_hubs)),
            )

    def _load_inbound_counts(self) -> dict[str, int]:
        rows = self._session.execute(
            select(SiteEdge.to_page_key, func.count()).group_by(SiteEdge.to_page_key)
        ).all()
        return {page_key: int(count) for page_key, count in rows}

    def _group_inbound(self, nodes: list[SiteNode]) -> int:
        return sum(self._inbound_by_key.get(node.page_key, 0) for node in nodes)

    def _section_pattern_key(self, node: SiteNode, section_key: str) -> str:
        if node.page_type == "listing":
            return f"listing:{section_key}"
        if node.page_type in ("ad_detail", "detail"):
            return node.url_pattern
        pattern = node.url_pattern or ""
        if "detail-{id}" in pattern:
            return pattern
        return pattern

    def _is_primary_pattern(self, pattern_key: str, nodes: list[SiteNode]) -> bool:
        if pattern_key.startswith(("listing:", "other:")):
            return True
        page_type = self._dominant_page_type(nodes)
        return page_type in _SECTION_PATTERN_TYPES or "detail-{id}" in pattern_key

    def _listing_label(self, section_key: str) -> str:
        return f"لیست: /{section_key}/{{brand}}"

    def _is_section_pattern_node(self, node: SiteNode) -> bool:
        if node.page_type in _SECTION_PATTERN_TYPES:
            return True
        pattern = node.url_pattern or ""
        return "detail-{id}" in pattern or pattern.endswith("/{id}")

    def _dominant_page_type(self, nodes: list[SiteNode]) -> str | None:
        counts: dict[str, int] = defaultdict(int)
        for node in nodes:
            counts[node.page_type] += 1
        if not counts:
            return None
        return max(counts.keys(), key=lambda key: counts[key])

    def _prefix_sort_key(self, nodes: list[SiteNode]) -> int:
        return self._group_inbound(nodes) * 1000 + len(nodes)

    def _upsert(
        self,
        *,
        group_key: str,
        parent_group_key: str | None,
        group_kind: str,
        label: str,
        section: str | None,
        path_prefix: str | None,
        url_pattern: str | None,
        page_type: str | None,
        page_count: int,
        weight: int,
        inbound_link_count: int,
        representative: SiteNode | None,
        depth: int,
        sort_order: int,
    ) -> None:
        self._groups.upsert(
            group_key=group_key,
            parent_group_key=parent_group_key,
            group_kind=group_kind,
            label=label,
            section=section,
            path_prefix=path_prefix,
            url_pattern=url_pattern,
            page_type=page_type,
            page_count=page_count,
            weight=weight,
            inbound_link_count=inbound_link_count,
            representative_page_key=representative.page_key if representative else None,
            representative_url=representative.url if representative else None,
            depth=depth,
            sort_order=sort_order,
        )

    def _path_prefix(self, node: SiteNode) -> str:
        path = urlparse(node.url).path.rstrip("/") or "/"
        segments = [s for s in path.split("/") if s]
        if not segments:
            return "/"
        depth = min(PATH_HUB_DEPTH, len(segments))
        return "/" + "/".join(segments[:depth])

    def _path_label(self, prefix: str, rep: SiteNode | None) -> str:
        if rep and rep.title and rep.page_type in _HUB_PAGE_TYPES:
            return rep.title[:80]
        tail = prefix.rstrip("/").split("/")[-1]
        return tail or prefix

    def _pattern_label(self, pattern: str, page_type: str | None) -> str:
        path = urlparse(pattern).path or pattern
        type_label = _TYPE_LABELS.get(page_type or "", page_type or "صفحه")
        return f"{type_label}: {path}"

    def _safe_key(self, value: str) -> str:
        return value.replace("|", "_").replace(":", "_")[:120]

    def _pick_representative(self, nodes: list[SiteNode]) -> SiteNode | None:
        if not nodes:
            return None

        def rank(node: SiteNode) -> tuple:
            hub_bonus = 0 if node.page_type in _HUB_PAGE_TYPES else 1
            return (node.depth, hub_bonus, node.page_key)

        return min(nodes, key=rank)

    def _node_weight(self, node: SiteNode) -> int:
        rule = self._config.match_route_rule(node.url, node.url_pattern)
        if rule is not None:
            return rule.weight
        meta_weight = (node.meta or {}).get("weight")
        if isinstance(meta_weight, int):
            return meta_weight
        return self._config.section_weight_for_url(node.url)

    def _sort_key(self, weight: int, page_count: int, inbound: int = 0) -> int:
        return -(weight * 1_000_000 + min(inbound, 999) * 1000 + min(page_count, 999_999))
