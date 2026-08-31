from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.crawl_job import CrawlJob, CrawlJobType
from app.models.search import Search
from app.models.site_map import SiteNode
from app.models.taxonomy import SearchBootstrapMetric, TaxonomyTerm
from app.repositories.taxonomy_repository import TaxonomyRepository

LOW_YIELD_THRESHOLD = 5


@dataclass
class TableCount:
    table: str
    count: int


@dataclass
class SiteCoverageRow:
    section: str
    page_type: str
    count: int


@dataclass
class DepthCount:
    depth: int
    count: int


@dataclass
class CrawlHealthSummary:
    total_jobs: int
    completed: int
    failed: int
    running: int
    site_map_jobs: int
    avg_pages_discovered: float
    avg_pages_crawled: float


@dataclass
class LastSiteMapJob:
    job_id: Optional[str] = None
    status: Optional[str] = None
    pages_crawled: int = 0
    pages_discovered: int = 0
    pages_failed: int = 0
    started_at: Optional[str] = None
    finished_at: Optional[str] = None


@dataclass
class StatsOverview:
    table_counts: list[TableCount] = field(default_factory=list)
    site_coverage: list[SiteCoverageRow] = field(default_factory=list)
    depth_distribution: list[DepthCount] = field(default_factory=list)
    taxonomy_active_brands: int = 0
    taxonomy_active_models: int = 0
    taxonomy_stale_terms: int = 0
    last_site_map_job: LastSiteMapJob = field(default_factory=LastSiteMapJob)
    crawl_health: CrawlHealthSummary = field(default_factory=CrawlHealthSummary)


@dataclass
class SearchDiscoveryRow:
    search_id: int
    name: Optional[str]
    brand: Optional[str]
    model: Optional[str]
    section_key: str
    enabled: bool
    bootstrapped_at: Optional[str]
    listing_url: Optional[str]
    pages_crawled: int
    ads_found: int
    matching_count: int
    match_rate: Optional[float]
    low_yield: bool
    metric_at: Optional[str]


class StatsService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def table_counts(self) -> list[TableCount]:
        tables = [
            "site_nodes",
            "site_edges",
            "site_sections",
            "site_map_groups",
            "taxonomy_terms",
            "taxonomy_refs",
            "search_bootstrap_metrics",
            "advertisements",
            "searches",
            "crawl_jobs",
        ]
        return [TableCount(table=table, count=self._count_table(table)) for table in tables]

    def _count_table(self, table: str) -> int:
        mapping = {
            "site_nodes": SiteNode,
            "taxonomy_terms": TaxonomyTerm,
            "search_bootstrap_metrics": SearchBootstrapMetric,
            "searches": Search,
            "crawl_jobs": CrawlJob,
        }
        model = mapping.get(table)
        if model is None:
            from sqlalchemy import text

            try:
                return int(self._session.scalar(text(f"SELECT COUNT(*) FROM {table}")) or 0)
            except Exception:
                return 0
        return int(self._session.scalar(select(func.count()).select_from(model)) or 0)

    def get_overview(self) -> StatsOverview:
        taxonomy = TaxonomyRepository(self._session)
        coverage_rows = self._session.execute(
            select(
                func.coalesce(SiteNode.section, "(none)"),
                SiteNode.page_type,
                func.count(),
            )
            .group_by(SiteNode.section, SiteNode.page_type)
            .order_by(func.count().desc())
            .limit(30)
        ).all()

        depth_rows = self._session.execute(
            select(SiteNode.depth, func.count())
            .group_by(SiteNode.depth)
            .order_by(SiteNode.depth)
        ).all()

        last_site_map = self._session.scalar(
            select(CrawlJob)
            .where(CrawlJob.job_type == CrawlJobType.SITE_MAP.value)
            .order_by(CrawlJob.created_at.desc())
            .limit(1)
        )

        completed = self._session.scalar(
            select(func.count()).select_from(CrawlJob).where(CrawlJob.status == "completed")
        )
        failed = self._session.scalar(
            select(func.count()).select_from(CrawlJob).where(CrawlJob.status == "failed")
        )
        running = self._session.scalar(
            select(func.count())
            .select_from(CrawlJob)
            .where(CrawlJob.status.in_(["running", "pending", "paused"]))
        )
        site_map_count = self._session.scalar(
            select(func.count())
            .select_from(CrawlJob)
            .where(CrawlJob.job_type == CrawlJobType.SITE_MAP.value)
        )
        avg_discovered = self._session.scalar(select(func.avg(CrawlJob.pages_discovered))) or 0.0
        avg_crawled = self._session.scalar(select(func.avg(CrawlJob.pages_crawled))) or 0.0

        last_job_info = LastSiteMapJob()
        if last_site_map:
            last_job_info = LastSiteMapJob(
                job_id=last_site_map.id,
                status=last_site_map.status,
                pages_crawled=last_site_map.pages_crawled,
                pages_discovered=last_site_map.pages_discovered,
                pages_failed=last_site_map.pages_failed,
                started_at=_iso(last_site_map.started_at),
                finished_at=_iso(last_site_map.finished_at),
            )

        return StatsOverview(
            table_counts=self.table_counts(),
            site_coverage=[
                SiteCoverageRow(section=row[0], page_type=row[1], count=row[2]) for row in coverage_rows
            ],
            depth_distribution=[DepthCount(depth=row[0], count=row[1]) for row in depth_rows],
            taxonomy_active_brands=taxonomy.count_active_terms(term_type="brand"),
            taxonomy_active_models=taxonomy.count_active_terms(term_type="model"),
            taxonomy_stale_terms=taxonomy.count_stale_terms(),
            last_site_map_job=last_job_info,
            crawl_health=CrawlHealthSummary(
                total_jobs=int(self._session.scalar(select(func.count()).select_from(CrawlJob)) or 0),
                completed=int(completed or 0),
                failed=int(failed or 0),
                running=int(running or 0),
                site_map_jobs=int(site_map_count or 0),
                avg_pages_discovered=float(avg_discovered),
                avg_pages_crawled=float(avg_crawled),
            ),
        )

    def get_search_discovery(self, *, threshold: int = LOW_YIELD_THRESHOLD) -> list[SearchDiscoveryRow]:
        searches = list(self._session.scalars(select(Search).order_by(Search.id)).all())
        rows: list[SearchDiscoveryRow] = []
        for search in searches:
            metric = self._session.scalar(
                select(SearchBootstrapMetric)
                .where(SearchBootstrapMetric.search_id == search.id)
                .order_by(SearchBootstrapMetric.created_at.desc())
                .limit(1)
            )
            ads_found = metric.ads_found if metric else 0
            matching = metric.matching_count if metric else 0
            match_rate = (matching / ads_found) if ads_found else None
            rows.append(
                SearchDiscoveryRow(
                    search_id=search.id,
                    name=search.name,
                    brand=search.brand,
                    model=search.model,
                    section_key=getattr(search, "section_key", "car") or "car",
                    enabled=search.enabled,
                    bootstrapped_at=_iso(search.bootstrapped_at),
                    listing_url=metric.listing_url if metric else None,
                    pages_crawled=metric.pages_crawled if metric else 0,
                    ads_found=ads_found,
                    matching_count=matching,
                    match_rate=match_rate,
                    low_yield=bool(metric and matching < threshold),
                    metric_at=_iso(metric.created_at) if metric else None,
                )
            )
        return rows


def _iso(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    return value.isoformat()


def overview_to_dict(overview: StatsOverview) -> dict[str, Any]:
    return {
        "table_counts": [{"table": t.table, "count": t.count} for t in overview.table_counts],
        "site_coverage": [
            {"section": r.section, "page_type": r.page_type, "count": r.count}
            for r in overview.site_coverage
        ],
        "depth_distribution": [{"depth": d.depth, "count": d.count} for d in overview.depth_distribution],
        "taxonomy_active_brands": overview.taxonomy_active_brands,
        "taxonomy_active_models": overview.taxonomy_active_models,
        "taxonomy_stale_terms": overview.taxonomy_stale_terms,
        "last_site_map_job": overview.last_site_map_job.__dict__,
        "crawl_health": overview.crawl_health.__dict__,
    }


def search_discovery_to_dict(rows: list[SearchDiscoveryRow]) -> list[dict[str, Any]]:
    return [row.__dict__ for row in rows]
