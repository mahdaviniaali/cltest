from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass
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
from crawler.domain.robots import extract_sitemap_directives, robots_url_for, sitemap_url_for
from crawler.domain.url_identity import compute_page_key, content_hash, ensure_http_url, normalize_url
from crawler.domain.ports import PageFetcher

logger = logging.getLogger(__name__)

COMMIT_BATCH = 10


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

    def run(self) -> SiteMapCrawlResult:
        self._events.emit(job_id=self._job_id, event_type="job_started", payload={"seeds": self._seeds})
        queue: deque[tuple[str, int, Optional[str]]] = deque()
        queued: set[str] = set()

        pending = self._visited.list_pending(self._job_id)
        if pending:
            for row in pending:
                parent_key = None
                self._enqueue(queue, queued, row.url, row.depth, parent_key)
        else:
            for seed in self._seeds:
                self._enqueue(queue, queued, seed, 0, None)
            self._seed_from_sitemaps(queue, queued)

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

            url, depth, parent_key = queue.popleft()
            normalized = normalize_url(url)
            if not normalized:
                continue
            page_key = compute_page_key(normalized)

            if not url_in_scope(normalized, self._policy, seed=self._seed):
                self._mark_skipped(normalized, page_key, depth, parent_key, "out_of_scope")
                continue

            if self._visited.is_visited(page_key):
                continue

            self._visited.mark_pending(url=normalized, page_key=page_key, job_id=self._job_id, depth=depth)
            self._pages_discovered += 1

            html = self._fetcher.fetch(normalized)
            if not html:
                self._pages_failed += 1
                self._visited.mark_failed(page_key, self._job_id, "fetch_failed")
                self._nodes.upsert(
                    page_key=page_key,
                    url=normalized,
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
                    payload={"url": normalized, "reason": "fetch_failed"},
                )
                self._maybe_commit()
                continue

            classification = self._classifier.classify(html, url=normalized)
            body_hash = content_hash(html)
            links = self._link_extractor.extract(html, base_url=normalized)

            self._nodes.upsert(
                page_key=page_key,
                url=normalized,
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
                meta={"link_count": len(links)},
            )
            self._visited.mark_crawled(page_key, self._job_id)
            self._pages_crawled += 1

            if classification.section:
                self._events.emit(
                    job_id=self._job_id,
                    event_type="section_detected",
                    payload={
                        "url": normalized,
                        "section": classification.section,
                        "page_type": classification.page_type,
                    },
                )

            self._events.emit(
                job_id=self._job_id,
                event_type="page_fetched",
                payload={
                    "url": normalized,
                    "page_type": classification.page_type,
                    "section": classification.section,
                    "depth": depth,
                    "links": len(links),
                },
            )

            if depth < self._policy.max_depth:
                for link in links:
                    child_norm = normalize_url(link.url)
                    if not child_norm or child_norm in queued:
                        continue
                    if not url_in_scope(child_norm, self._policy, seed=self._seed):
                        continue
                    child_key = compute_page_key(child_norm)
                    self._edges.add_edge(
                        from_page_key=page_key,
                        to_page_key=child_key,
                        relation_type="internal_link",
                        job_id=self._job_id,
                    )
                    self._enqueue(queue, queued, child_norm, depth + 1, page_key)

            self._update_progress()
            self._maybe_commit()

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

    def _enqueue(
        self,
        queue: deque[tuple[str, int, Optional[str]]],
        queued: set[str],
        url: str,
        depth: int,
        parent_key: Optional[str],
    ) -> None:
        normalized = normalize_url(url)
        if not normalized or normalized in queued:
            return
        queued.add(normalized)
        queue.append((normalized, depth, parent_key))

    def _seed_from_sitemaps(
        self,
        queue: deque[tuple[str, int, Optional[str]]],
        queued: set[str],
    ) -> None:
        raw_fetcher = self._resolve_http_fetcher()
        if raw_fetcher is None:
            return

        sitemap_candidates = [sitemap_url_for(self._seed)]
        robots_text = raw_fetcher.fetch_raw(robots_url_for(self._seed))
        if robots_text:
            sitemap_candidates.extend(extract_sitemap_directives(robots_text))

        seen_sitemaps: set[str] = set()
        for sm_url in sitemap_candidates:
            if sm_url in seen_sitemaps:
                continue
            seen_sitemaps.add(sm_url)
            xml = raw_fetcher.fetch_raw(sm_url)
            if not xml:
                continue
            for loc in parse_sitemap_locs(xml):
                norm = normalize_url(loc)
                if norm and url_in_scope(norm, self._policy, seed=self._seed):
                    self._enqueue(queue, queued, norm, 0, None)
                    child_key = compute_page_key(norm)
                    self._edges.add_edge(
                        from_page_key=compute_page_key(self._seed),
                        to_page_key=child_key,
                        relation_type="sitemap",
                        job_id=self._job_id,
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
            url_pattern="",
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
            payload={"url": url, "reason": reason},
        )

    def _update_progress(self) -> None:
        job = self._jobs.get(self._job_id)
        if job:
            self._jobs.update_site_map_progress(
                job,
                pages_crawled=self._pages_crawled,
                pages_discovered=self._pages_discovered,
                pages_failed=self._pages_failed,
            )

    def _maybe_commit(self) -> None:
        if self._pages_crawled % COMMIT_BATCH == 0:
            self._update_progress()
            self._session.commit()
