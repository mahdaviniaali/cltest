from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.site_map import SiteEdge, SiteNode, SiteNodeStatus
from crawler.domain.page_classification import classify_node, classify_url


class SiteNodeRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, page_key: str) -> Optional[SiteNode]:
        return self._session.get(SiteNode, page_key)

    def upsert(
        self,
        *,
        page_key: str,
        url: str,
        url_pattern: str,
        depth: int,
        parent_page_key: Optional[str],
        page_type: str,
        section: Optional[str],
        title: Optional[str],
        excerpt: Optional[str],
        status: str,
        content_hash: Optional[str],
        job_id: str,
        meta: Optional[dict[str, Any]] = None,
    ) -> SiteNode:
        node = self.get(page_key)
        now = datetime.now(timezone.utc)
        if node is None:
            node = SiteNode(
                page_key=page_key,
                url=url,
                url_pattern=url_pattern,
                depth=depth,
                parent_page_key=parent_page_key,
                page_type=page_type,
                section=section,
                title=title,
                excerpt=excerpt,
                status=status,
                content_hash=content_hash,
                last_crawled_at=now if status == SiteNodeStatus.CRAWLED.value else None,
                last_job_id=job_id,
                meta=meta,
            )
            self._session.add(node)
        else:
            node.url = url
            node.url_pattern = url_pattern
            node.depth = min(node.depth, depth) if node.depth else depth
            if parent_page_key and not node.parent_page_key:
                node.parent_page_key = parent_page_key
            node.page_type = page_type
            if section:
                node.section = section
            if title:
                node.title = title
            if excerpt:
                node.excerpt = excerpt
            node.status = status
            if content_hash:
                node.content_hash = content_hash
            if status == SiteNodeStatus.CRAWLED.value:
                node.last_crawled_at = now
            node.last_job_id = job_id
            if meta:
                node.meta = {**(node.meta or {}), **meta}
        self._session.flush()
        return node

    def list_all(self, *, section: Optional[str] = None, limit: int = 5000) -> list[SiteNode]:
        stmt = select(SiteNode).order_by(SiteNode.depth, SiteNode.url).limit(limit)
        if section:
            stmt = stmt.where(SiteNode.section == section)
        return list(self._session.scalars(stmt).all())

    def count(self, *, section: Optional[str] = None) -> int:
        stmt = select(func.count()).select_from(SiteNode)
        if section:
            stmt = stmt.where(SiteNode.section == section)
        return int(self._session.scalar(stmt) or 0)

    def count_by_section(self) -> dict[str, int]:
        nodes = self.list_all(limit=100_000)
        counts: dict[str, int] = {}
        for node in nodes:
            key = node.section or "unknown"
            counts[key] = counts.get(key, 0) + 1
        return counts

    def ensure_discovered(
        self,
        *,
        page_key: str,
        url: str,
        depth: int,
        parent_page_key: Optional[str],
        job_id: str,
        weight: Optional[int] = None,
        config: Optional[object] = None,
    ) -> None:
        """Record a discovered URL so later incremental runs can resume the frontier."""
        if self.get(page_key) is not None:
            return
        from config.bama_site import BamaSiteConfig, load_bama_site_config

        site_config = config if isinstance(config, BamaSiteConfig) else load_bama_site_config()
        page_type, section, url_pattern = classify_url(url, site_config)
        meta: dict[str, object] = {}
        if weight is not None:
            meta["weight"] = weight
        self._session.add(
            SiteNode(
                page_key=page_key,
                url=url,
                url_pattern=url_pattern,
                depth=depth,
                parent_page_key=parent_page_key,
                page_type=page_type,
                section=section,
                title=None,
                excerpt=None,
                status=SiteNodeStatus.DISCOVERED.value,
                content_hash=None,
                last_job_id=job_id,
                meta=meta or None,
            )
        )
        self._session.flush()

    def list_uncrawled_frontier(
        self,
        *,
        limit: int,
        max_depth: int,
        is_visited: Callable[[str], bool],
    ) -> list[SiteNode]:
        stmt = (
            select(SiteNode)
            .where(SiteNode.depth <= max_depth)
            .order_by(SiteNode.depth, SiteNode.url)
            .limit(limit * 4)
        )
        candidates = [n for n in self._session.scalars(stmt).all() if not is_visited(n.page_key)]
        candidates.sort(
            key=lambda node: (
                node.depth,
                -int((node.meta or {}).get("weight") or 0),
                node.url,
            )
        )
        return candidates[:limit]

    def reclassify_discovered(self, config: object) -> int:
        """Fix page_type/section/url_pattern on discovered frontier rows (URL-only)."""
        return self.reclassify_nodes(
            config,
            statuses=[SiteNodeStatus.DISCOVERED.value],
        )

    def reclassify_nodes(
        self,
        config: object,
        *,
        statuses: list[str] | None = None,
    ) -> int:
        """Re-apply URL-based classification (uses stored title when present)."""
        from config.bama_site import BamaSiteConfig, load_bama_site_config
        from crawler.domain.link_scorer import score_url

        if not isinstance(config, BamaSiteConfig):
            config = load_bama_site_config()

        stmt = select(SiteNode)
        if statuses:
            stmt = stmt.where(SiteNode.status.in_(statuses))
        updated = 0
        for node in self._session.scalars(stmt).all():
            page_type, section, url_pattern = classify_node(
                node.url,
                config,
                title=node.title,
            )
            weight = score_url(node.url, config, inferred_pattern=url_pattern)
            meta = {**(node.meta or {}), "weight": weight}
            changed = (
                node.page_type != page_type
                or node.section != section
                or node.url_pattern != url_pattern
                or (node.meta or {}).get("weight") != weight
            )
            if changed:
                node.page_type = page_type
                node.section = section
                node.url_pattern = url_pattern
                node.meta = meta
                updated += 1
        if updated:
            self._session.flush()
        return updated


class SiteEdgeRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add_edge(
        self,
        *,
        from_page_key: str,
        to_page_key: str,
        relation_type: str = "internal_link",
        job_id: Optional[str] = None,
    ) -> None:
        existing = self._session.scalar(
            select(SiteEdge).where(
                SiteEdge.from_page_key == from_page_key,
                SiteEdge.to_page_key == to_page_key,
            )
        )
        if existing:
            return
        self._session.add(
            SiteEdge(
                from_page_key=from_page_key,
                to_page_key=to_page_key,
                relation_type=relation_type,
                job_id=job_id,
            )
        )
        self._session.flush()

    def list_edges(self, *, limit: int = 10000) -> list[SiteEdge]:
        stmt = select(SiteEdge).limit(limit)
        return list(self._session.scalars(stmt).all())
