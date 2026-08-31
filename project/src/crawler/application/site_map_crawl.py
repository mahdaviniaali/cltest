from __future__ import annotations

import heapq
import logging
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy.orm import Session

from app.models.crawl_job import CrawlJobStatus
from app.models.site_map import SiteNodeStatus
from app.repositories.crawl_event_repository import CrawlEventRepository
from app.repositories.crawl_job_repository import CrawlJobRepository
from app.repositories.site_node_repository import SiteEdgeRepository, SiteNodeRepository
from app.repositories.visited_url_repository import VisitedUrlRepository
from config.bama_site import BamaSiteConfig, load_bama_site_config
from crawler.adapters.bama.page_classifier import BamaPageClassifier
from crawler.adapters.http_page_fetcher import HttpPageFetcher
from crawler.adapters.link_extractor import LinkExtractor
from crawler.application.site_catalog_builder import SiteCatalogBuilder
from crawler.core.http_client import HttpClient
from crawler.domain.crawl_policy import CrawlPolicy, parse_sitemap_locs, url_in_scope
from crawler.domain.link_scorer import score_url
from crawler.domain.robots import extract_sitemap_directives, robots_url_for, sitemap_url_for
from crawler.domain.url_identity import (
    canonicalize_url,
    compute_page_key,
    content_hash,
    ensure_http_url,
    normalize_url,
)
from crawler.domain.url_patterns import infer_url_pattern
from crawler.domain.ports import PageFetcher

logger = logging.getLogger(__name__)

COMMIT_BATCH = 10


@dataclass(order=True, slots=True)
class _QueueEntry:
    sort_key: tuple[int, int, int]
    url: str = field(compare=False)
    depth: int = field(compare=False)
    parent_key: Optional[str] = field(compare=False, default=None)
    weight: int = field(compare=False, default=1)


@dataclass(slots=True)
class SiteMapCrawlResult:
    pages_crawled: int
    pages_discovered: int
    pages_failed: int
    stopped_reason: str


class SiteMapCrawlService:
    def __init__(
        self,
        session: Session,
        fetcher: PageFetcher,
        *,
        job_id: str,
        config: Optional[BamaSiteConfig] = None,
        max_pages: Optional[int] = None,
        max_depth: Optional[int] = None,
        seed_urls: Optional[list[str]] = None,
    ) -> None:
        self._session = session
        self._fetcher = fetcher
        self._job_id = job_id
        self._config = config or load_bama_site_config()
        self._policy: CrawlPolicy = self._config.to_crawl_policy()
        if max_pages is not None:
            self._policy.max_pages = max_pages
        if max_depth is not None:
            self._policy.max_depth = max_depth
        self._seeds = [ensure_http_url(u) for u in (seed_urls or self._config.seed_urls)]
        self._seed = self._seeds[0]

        self._jobs = CrawlJobRepository(session)
        self._nodes = SiteNodeRepository(session)
        self._edges = SiteEdgeRepository(session)
        self._visited = VisitedUrlRepository(session)
        self._events = CrawlEventRepository(session)
        self._link_extractor = LinkExtractor()
        self._classifier = BamaPageClassifier(self._config)

        self._pages_crawled = 0
        self._pages_discovered = 0
        self._pages_failed = 0
        self._seq = 0
        self._depth_one_bootstrapped = False
        self._deferred_sitemap: list[tuple[str, int]] = []
        self._deferred_flushed = False

        self._current_depth = 0
        self._level_pages = 0
        self._level_sections: set[str] = set()

    def run(self) -> SiteMapCrawlResult:
        self._events.emit(job_id=self._job_id, event_type="job_started", payload={"seeds": self._seeds})
        queue: list[_QueueEntry] = []
        queued_keys: set[str] = set()

        pending = self._visited.list_pending(self._job_id)
        if pending:
            for row in pending:
                canonical = self._canonical(row.url)
                if not canonical:
                    continue
                weight = score_url(canonical, self._config)
                self._push(queue, queued_keys, canonical, row.depth, None, weight)
        else:
            home_key = compute_page_key(self._canonical(self._seed) or self._seed)
            for seed in self._seeds:
                weight = score_url(seed, self._config)
                self._push(queue, queued_keys, seed, 0, None, weight)
            # Always bootstrap section roots + sitemap even when home was crawled in a prior job.
            incremental = self._visited.is_visited(home_key)
            self._bootstrap_depth_one(queue, queued_keys, home_key, full_sitemap_seed=incremental)
            self._seed_uncrawled_frontier(queue, queued_keys)

        stopped_reason = "completed"
        while queue and self._pages_crawled < self._policy.max_pages:
            status = self._poll_job_status()
            if status == CrawlJobStatus.CANCELLED.value:
                stopped_reason = "cancelled"
                break
            if status == CrawlJobStatus.PAUSED.value:
                self._events.emit(job_id=self._job_id, event_type="job_paused")
                stopped_reason = "paused"
                break

            entry = heapq.heappop(queue)
            self._maybe_advance_level(entry.depth, queue, queued_keys)

            url = entry.url
            depth = entry.depth
            parent_key = entry.parent_key

            canonical = self._canonical(url)
            if not canonical:
                continue
            page_key = compute_page_key(canonical)

            if not url_in_scope(canonical, self._policy, seed=self._seed):
                self._mark_skipped(canonical, page_key, depth, parent_key, "out_of_scope")
                continue

            if self._visited.is_visited(page_key):
                continue

            self._visited.mark_pending(url=canonical, page_key=page_key, job_id=self._job_id, depth=depth)
            self._pages_discovered += 1

            fetch_url = normalize_url(url) or canonical
            html = self._fetcher.fetch(fetch_url)
            if not html:
                self._pages_failed += 1
                self._visited.mark_failed(page_key, self._job_id, "fetch_failed")
                self._nodes.upsert(
                    page_key=page_key,
                    url=fetch_url,
                    url_pattern="",
                    depth=depth,
                    parent_page_key=parent_key,
                    page_type="unknown",
                    section=None,
                    title=None,
                    excerpt=None,
                    status=SiteNodeStatus.FAILED.value,
                    content_hash=None,
                    job_id=self._job_id,
                )
                self._events.emit(
                    job_id=self._job_id,
                    event_type="page_failed",
                    payload={"url": fetch_url, "reason": "fetch_failed", "depth": depth},
                )
                self._maybe_commit()
                continue

            classification = self._classifier.classify(html, url=fetch_url)
            body_hash = content_hash(html)
            links = self._link_extractor.extract(html, base_url=fetch_url)

            self._nodes.upsert(
                page_key=page_key,
                url=fetch_url,
                url_pattern=classification.url_pattern,
                depth=depth,
                parent_page_key=parent_key,
                page_type=classification.page_type,
                section=classification.section,
                title=classification.title,
                excerpt=classification.excerpt,
                status=SiteNodeStatus.CRAWLED.value,
                content_hash=body_hash,
                job_id=self._job_id,
                meta={"link_count": len(links), "weight": entry.weight},
            )
            self._visited.mark_crawled(page_key, self._job_id)
            self._pages_crawled += 1
            self._level_pages += 1
            if classification.section:
                self._level_sections.add(classification.section)

            if depth == 0 and not self._depth_one_bootstrapped:
                self._bootstrap_depth_one(queue, queued_keys, page_key)

            if classification.section:
                self._events.emit(
                    job_id=self._job_id,
                    event_type="section_detected",
                    payload={
                        "url": fetch_url,
                        "section": classification.section,
                        "page_type": classification.page_type,
                        "depth": depth,
                    },
                )

            self._events.emit(
                job_id=self._job_id,
                event_type="page_fetched",
                payload={
                    "url": fetch_url,
                    "page_type": classification.page_type,
                    "section": classification.section,
                    "depth": depth,
                    "weight": entry.weight,
                    "links": len(links),
                },
            )

            if depth < self._policy.max_depth:
                for link in links:
                    child_canonical = self._canonical(link.url)
                    if not child_canonical:
                        continue
                    child_key = compute_page_key(child_canonical)
                    if child_key in queued_keys:
                        continue
                    if not url_in_scope(child_canonical, self._policy, seed=self._seed):
                        continue
                    child_weight = score_url(child_canonical, self._config)
                    self._nodes.ensure_discovered(
                        page_key=child_key,
                        url=child_canonical,
                        depth=depth + 1,
                        parent_page_key=page_key,
                        job_id=self._job_id,
                        weight=child_weight,
                    )
                    self._edges.add_edge(
                        from_page_key=page_key,
                        to_page_key=child_key,
                        relation_type="internal_link",
                        job_id=self._job_id,
                    )
                    self._push(
                        queue,
                        queued_keys,
                        child_canonical,
                        depth + 1,
                        page_key,
                        child_weight,
                    )

            self._update_progress(depth)
            self._maybe_commit()

        if self._level_pages > 0:
            self._emit_level_completed(self._current_depth, queue, queued_keys)

        if stopped_reason == "completed":
            catalog = SiteCatalogBuilder(self._session, self._config)
            sections = catalog.build()
            self._events.emit(
                job_id=self._job_id,
                event_type="job_completed",
                payload={"sections": sections, "pages_crawled": self._pages_crawled},
            )

        self._session.commit()
        return SiteMapCrawlResult(
            pages_crawled=self._pages_crawled,
            pages_discovered=self._pages_discovered,
            pages_failed=self._pages_failed,
            stopped_reason=stopped_reason,
        )

    def _canonical(self, url: str) -> str | None:
        return canonicalize_url(url, self._config.canonical.strip_query_params)

    def _push(
        self,
        queue: list[_QueueEntry],
        queued_keys: set[str],
        url: str,
        depth: int,
        parent_key: Optional[str],
        weight: int,
    ) -> None:
        canonical = self._canonical(url)
        if not canonical:
            return
        page_key = compute_page_key(canonical)
        if page_key in queued_keys:
            return
        if self._visited.is_visited(page_key):
            return
        queued_keys.add(page_key)
        self._seq += 1
        sort_key = (depth, -weight, self._seq)
        heapq.heappush(
            queue,
            _QueueEntry(
                sort_key=sort_key,
                url=canonical,
                depth=depth,
                parent_key=parent_key,
                weight=weight,
            ),
        )

    def _bootstrap_depth_one(
        self,
        queue: list[_QueueEntry],
        queued_keys: set[str],
        home_key: str,
        *,
        full_sitemap_seed: bool = False,
    ) -> None:
        if self._depth_one_bootstrapped:
            return
        self._depth_one_bootstrapped = True
        for root in self._config.section_roots:
            url = ensure_http_url(root.url)
            child_key = compute_page_key(self._canonical(url) or url)
            self._nodes.ensure_discovered(
                page_key=child_key,
                url=self._canonical(url) or url,
                depth=1,
                parent_page_key=home_key,
                job_id=self._job_id,
                weight=root.weight,
            )
            self._edges.add_edge(
                from_page_key=home_key,
                to_page_key=child_key,
                relation_type="section_root",
                job_id=self._job_id,
            )
            self._push(queue, queued_keys, url, 1, home_key, root.weight)
        self._collect_sitemap_urls(
            queue,
            queued_keys,
            home_key,
            full_seed=full_sitemap_seed,
        )
        if full_sitemap_seed:
            self._flush_deferred(queue, queued_keys)

    def _seed_uncrawled_frontier(
        self,
        queue: list[_QueueEntry],
        queued_keys: set[str],
    ) -> None:
        seed_budget = max(self._policy.max_pages * 3, 100)
        frontier = self._nodes.list_uncrawled_frontier(
            limit=seed_budget,
            max_depth=self._policy.max_depth,
            is_visited=self._visited.is_visited,
        )
        for node in frontier:
            weight = int((node.meta or {}).get("weight") or score_url(node.url, self._config))
            self._push(
                queue,
                queued_keys,
                node.url,
                node.depth,
                node.parent_page_key,
                weight,
            )

    def _collect_sitemap_urls(
        self,
        queue: list[_QueueEntry],
        queued_keys: set[str],
        home_key: str,
        *,
        full_seed: bool = False,
    ) -> None:
        raw_fetcher = self._resolve_http_fetcher()
        if raw_fetcher is None:
            return

        sitemap_candidates = [sitemap_url_for(self._seed)]
        robots_text = raw_fetcher.fetch_raw(robots_url_for(self._seed))
        if robots_text:
            sitemap_candidates.extend(extract_sitemap_directives(robots_text))

        seen_sitemaps: set[str] = set()
        collected: list[tuple[str, int]] = []
        for sm_url in sitemap_candidates:
            if sm_url in seen_sitemaps:
                continue
            seen_sitemaps.add(sm_url)
            xml = raw_fetcher.fetch_raw(sm_url)
            if not xml:
                continue
            for loc in parse_sitemap_locs(xml):
                norm = self._canonical(loc)
                if not norm or not url_in_scope(norm, self._policy, seed=self._seed):
                    continue
                weight = score_url(norm, self._config)
                collected.append((norm, weight))

        collected.sort(key=lambda item: -item[1])
        cap = self._config.sitemap_max_urls
        if full_seed:
            cap = max(cap, self._policy.max_pages * 3)
        immediate = collected[:cap]
        deferred = collected[cap:] if self._config.sitemap_defer and not full_seed else []

        for norm, weight in immediate:
            child_key = compute_page_key(norm)
            self._nodes.ensure_discovered(
                page_key=child_key,
                url=norm,
                depth=1,
                parent_page_key=home_key,
                job_id=self._job_id,
                weight=weight,
            )
            self._edges.add_edge(
                from_page_key=home_key,
                to_page_key=child_key,
                relation_type="sitemap",
                job_id=self._job_id,
            )
            self._push(queue, queued_keys, norm, 1, home_key, weight)

        for norm, weight in deferred:
            self._deferred_sitemap.append((norm, max(1, weight // 2)))

    def _flush_deferred(
        self,
        queue: list[_QueueEntry],
        queued_keys: set[str],
    ) -> None:
        if self._deferred_flushed or not self._deferred_sitemap:
            return
        self._deferred_flushed = True
        home_key = compute_page_key(self._canonical(self._seed) or self._seed)
        for norm, weight in self._deferred_sitemap:
            child_key = compute_page_key(norm)
            if child_key in queued_keys:
                continue
            self._edges.add_edge(
                from_page_key=home_key,
                to_page_key=child_key,
                relation_type="sitemap_deferred",
                job_id=self._job_id,
            )
            self._push(queue, queued_keys, norm, 1, home_key, weight)

    def _maybe_advance_level(
        self,
        next_depth: int,
        queue: list[_QueueEntry],
        queued_keys: set[str],
    ) -> None:
        if next_depth > self._current_depth and self._level_pages > 0:
            self._emit_level_completed(self._current_depth, queue, queued_keys)
            self._current_depth = next_depth
            self._level_pages = 0
            self._level_sections = set()
        elif next_depth > self._current_depth:
            if self._current_depth == 1:
                self._flush_deferred(queue, queued_keys)
            self._current_depth = next_depth

    def _emit_level_completed(
        self,
        depth: int,
        queue: list[_QueueEntry],
        queued_keys: set[str],
    ) -> None:
        if depth == 1:
            self._flush_deferred(queue, queued_keys)
        self._events.emit(
            job_id=self._job_id,
            event_type="level_completed",
            payload={
                "depth": depth,
                "pages_at_level": self._level_pages,
                "sections_seen": sorted(self._level_sections),
            },
        )

    def _resolve_http_fetcher(self) -> HttpPageFetcher | None:
        fetcher: PageFetcher = self._fetcher
        while True:
            if isinstance(fetcher, HttpPageFetcher):
                return fetcher
            inner = getattr(fetcher, "_inner", None)
            if inner is None:
                return None
            fetcher = inner

    def _poll_job_status(self) -> str:
        self._session.expire_all()
        job = self._jobs.get(self._job_id)
        return job.status if job else CrawlJobStatus.CANCELLED.value

    def _mark_skipped(
        self,
        url: str,
        page_key: str,
        depth: int,
        parent_key: Optional[str],
        reason: str,
    ) -> None:
        self._visited.mark_pending(url=url, page_key=page_key, job_id=self._job_id, depth=depth)
        self._visited.mark_skipped(page_key, self._job_id)
        self._nodes.upsert(
            page_key=page_key,
            url=url,
            url_pattern=infer_url_pattern(url),
            depth=depth,
            parent_page_key=parent_key,
            page_type="unknown",
            section=None,
            title=None,
            excerpt=None,
            status=SiteNodeStatus.SKIPPED.value,
            content_hash=None,
            job_id=self._job_id,
            meta={"skip_reason": reason},
        )
        self._events.emit(
            job_id=self._job_id,
            event_type="page_skipped",
            payload={"url": url, "reason": reason, "depth": depth},
        )

    def _update_progress(self, current_depth: int) -> None:
        job = self._jobs.get(self._job_id)
        if job:
            self._jobs.update_site_map_progress(
                job,
                pages_crawled=self._pages_crawled,
                pages_discovered=self._pages_discovered,
                pages_failed=self._pages_failed,
                current_depth=current_depth,
            )

    def _maybe_commit(self) -> None:
        if self._pages_crawled % COMMIT_BATCH == 0:
            self._update_progress(self._current_depth)
            self._session.commit()
