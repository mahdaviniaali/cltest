from __future__ import annotations

from collections import defaultdict
from typing import Optional
from urllib.parse import urlparse
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.crawl_job import CrawlJobStatus, CrawlJobType
from app.repositories.crawl_event_repository import CrawlEventRepository
from app.repositories.crawl_job_repository import CrawlJobRepository
from app.repositories.site_node_repository import SiteEdgeRepository, SiteNodeRepository
from app.repositories.site_section_repository import SiteSectionRepository
from app.schemas.inspector import SiteTreeNode


class InspectorService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._jobs = CrawlJobRepository(session)
        self._nodes = SiteNodeRepository(session)
        self._edges = SiteEdgeRepository(session)
        self._events = CrawlEventRepository(session)
        self._sections = SiteSectionRepository(session)

    def start_site_map(
        self,
        *,
        triggered_by: str,
        max_pages: Optional[int] = None,
        max_depth: Optional[int] = None,
    ) -> tuple[object, bool]:
        running = self._jobs.get_running_site_map()
        if running is not None:
            return running, True

        job = self._jobs.create(
            job_type=CrawlJobType.SITE_MAP.value,
            triggered_by=triggered_by,
            idempotency_key=f"site_map:{triggered_by}:{uuid4()}",
        )
        self._session.commit()
        return job, False

    def pause_job(self, job_id: str) -> Optional[object]:
        job = self._jobs.get(job_id)
        if job is None or job.status != CrawlJobStatus.RUNNING.value:
            return job
        return self._jobs.mark_paused(job)

    def resume_job(self, job_id: str) -> Optional[object]:
        job = self._jobs.get(job_id)
        if job is None or job.status != CrawlJobStatus.PAUSED.value:
            return job
        return self._jobs.mark_resumed(job)

    def cancel_job(self, job_id: str) -> Optional[object]:
        job = self._jobs.get(job_id)
        if job is None or job.status not in {
            CrawlJobStatus.RUNNING.value,
            CrawlJobStatus.PAUSED.value,
            CrawlJobStatus.PENDING.value,
        }:
            return job
        return self._jobs.mark_cancelled(job)

    def build_tree(self, *, section: Optional[str] = None) -> list[SiteTreeNode]:
        nodes = self._nodes.list_all(section=section, limit=5000)
        tree_root: dict[str, dict] = {}

        for node in nodes:
            parsed = urlparse(node.url)
            segments = [s for s in parsed.path.split("/") if s] or ["home"]
            cursor = tree_root
            path_acc = ""
            for idx, segment in enumerate(segments):
                path_acc += f"/{segment}"
                if segment not in cursor:
                    cursor[segment] = {
                        "path": path_acc,
                        "label": segment,
                        "page_key": None,
                        "page_type": None,
                        "section": None,
                        "children": {},
                    }
                if idx == len(segments) - 1:
                    cursor[segment]["page_key"] = node.page_key
                    cursor[segment]["page_type"] = node.page_type
                    cursor[segment]["section"] = node.section
                    if node.title:
                        cursor[segment]["label"] = node.title[:80]
                cursor = cursor[segment]["children"]

        return self._convert_tree(tree_root)

    def _convert_tree(self, node_map: dict[str, dict]) -> list[SiteTreeNode]:
        result: list[SiteTreeNode] = []
        for key in sorted(node_map.keys()):
            raw = node_map[key]
            result.append(
                SiteTreeNode(
                    path=raw["path"],
                    label=raw["label"],
                    page_key=raw.get("page_key"),
                    page_type=raw.get("page_type"),
                    section=raw.get("section"),
                    children=self._convert_tree(raw.get("children") or {}),
                )
            )
        return result

    def build_graph(
        self,
        *,
        section: Optional[str] = None,
        limit: int = 500,
    ) -> tuple[list, list]:
        nodes = self._nodes.list_all(section=section, limit=limit)
        node_keys = {n.page_key for n in nodes}
        edges = self._edges.list_edges(limit=limit * 5)
        filtered_edges = [
            {"from": e.from_page_key, "to": e.to_page_key, "type": e.relation_type}
            for e in edges
            if e.from_page_key in node_keys and e.to_page_key in node_keys
        ]
        return nodes, filtered_edges

    def get_page_detail(self, page_key: str) -> Optional[dict]:
        node = self._nodes.get(page_key)
        if node is None:
            return None
        edges = self._edges.list_edges(limit=10000)
        outbound = []
        node_by_key = {n.page_key: n for n in self._nodes.list_all(limit=10000)}
        for edge in edges:
            if edge.from_page_key != page_key:
                continue
            target = node_by_key.get(edge.to_page_key)
            outbound.append(
                {
                    "page_key": edge.to_page_key,
                    "url": target.url if target else "",
                    "relation_type": edge.relation_type,
                }
            )
        return {
            "node": node,
            "outbound_links": outbound,
        }
