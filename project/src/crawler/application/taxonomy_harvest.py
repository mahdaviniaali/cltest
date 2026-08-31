from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.models.site_map import SiteNodeStatus
from app.repositories.site_node_repository import SiteNodeRepository
from config.bama_site import BamaSiteConfig, load_bama_site_config
from config import settings
from crawler.adapters.http_page_fetcher import HttpPageFetcher
from crawler.application.taxonomy_builder import TaxonomyBuilder
from crawler.core.http_client import HttpClient
from crawler.domain.crawl_policy import parse_sitemap_locs
from crawler.domain.robots import extract_sitemap_directives, robots_url_for
from crawler.domain.taxonomy_labels import REVIEW_HUBS, apply_review_labels, lookup_review_names, parse_review_labels
from crawler.domain.taxonomy_urls import ClassifiedTaxonomyUrl, classify_taxonomy_urls
from crawler.domain.url_identity import compute_page_key
from crawler.domain.url_patterns import infer_url_pattern

logger = logging.getLogger(__name__)

_KNOWN_SITEMAPS = (
    "https://bama.ir/sitemap/car",
    "https://bama.ir/sitemap/motorcycle",
    "https://bama.ir/sitemap/truck",
)


class TaxonomyHarvestService:
    """Build the brand/model catalog from Bama filter sitemaps (robots-allowed)."""

    def __init__(
        self,
        session: Session,
        *,
        config: Optional[BamaSiteConfig] = None,
        fetcher: Optional[HttpPageFetcher] = None,
        http: Optional[HttpClient] = None,
    ) -> None:
        self._session = session
        self._config = config or load_bama_site_config()
        self._http = http
        self._owns_http = http is None and fetcher is None
        if fetcher is not None:
            self._fetcher = fetcher
        else:
            self._http = http or HttpClient(settings.USER_AGENT, timeout=settings.TIMEOUT)
            self._fetcher = HttpPageFetcher(
                self._http,
                user_agent=settings.USER_AGENT,
                respect_robots=True,
            )
        self._nodes = SiteNodeRepository(session)

    def harvest(self, *, job_id: str | None = None) -> dict:
        try:
            locs = self._collect_listing_urls()
            classified = classify_taxonomy_urls(locs)
            classified = apply_review_labels(classified, self._fetch_review_pages(classified))
            if not any(item.term_type == "brand" for item in classified):
                logger.warning("Taxonomy harvest found no brand URLs")
                return {"brands": 0, "models": 0, "snapshot_id": None, "skipped": True}

            self._persist_nodes(classified, job_id=job_id or "taxonomy-harvest")
            return TaxonomyBuilder(self._session, self._config, job_id=job_id).build()
        finally:
            if self._owns_http and self._http is not None:
                self._http.close()

    def _collect_listing_urls(self) -> list[str]:
        sitemap_urls = list(_KNOWN_SITEMAPS)
        robots_text = self._fetcher.fetch_raw(robots_url_for("https://bama.ir/"))
        if robots_text:
            for sm_url in extract_sitemap_directives(robots_text):
                if _is_taxonomy_sitemap(sm_url) and sm_url not in sitemap_urls:
                    sitemap_urls.append(sm_url)

        locs: list[str] = []
        seen: set[str] = set()
        for sm_url in sitemap_urls:
            xml = self._fetcher.fetch_raw(sm_url)
            if not xml:
                continue
            for loc in parse_sitemap_locs(xml):
                if loc in seen:
                    continue
                seen.add(loc)
                locs.append(loc)
        return locs

    def _fetch_review_pages(self, classified: list[ClassifiedTaxonomyUrl]) -> dict[str, list[str]]:
        pages: dict[str, list[str]] = {}
        catalogs: dict[str, dict] = {}
        for section, url in REVIEW_HUBS.items():
            html = self._get_html(url)
            if not html:
                continue
            pages[section] = [html]
            catalogs[section] = parse_review_labels(html)

        for item in classified:
            if item.term_type != "brand" or item.section not in pages:
                continue
            if lookup_review_names(catalogs[item.section], item) is None:
                continue
            html = self._get_html(f"{REVIEW_HUBS[item.section].rstrip('/')}/{item.slug}")
            if html:
                pages[item.section].append(html)
        return pages

    def _get_html(self, url: str) -> str | None:
        fetch = getattr(self._fetcher, "fetch", None)
        if callable(fetch):
            return fetch(url)
        return self._fetcher.fetch_raw(url)

    def _persist_nodes(self, classified: list[ClassifiedTaxonomyUrl], *, job_id: str) -> None:
        brand_keys: dict[tuple[str, str], str] = {}
        for item in classified:
            if item.term_type != "brand":
                continue
            page_key = compute_page_key(item.listing_url)
            brand_keys[(item.section, item.slug)] = page_key
            self._nodes.upsert(
                page_key=page_key,
                url=item.listing_url,
                url_pattern=infer_url_pattern(item.listing_url),
                depth=2,
                parent_page_key=None,
                page_type="brand_hub",
                section=item.section,
                title=item.label,
                excerpt=None,
                status=SiteNodeStatus.CRAWLED.value,
                content_hash=None,
                job_id=job_id,
                meta={"source": "taxonomy_sitemap"},
            )

        for item in classified:
            if item.term_type != "model":
                continue
            page_key = compute_page_key(item.listing_url)
            self._nodes.upsert(
                page_key=page_key,
                url=item.listing_url,
                url_pattern=infer_url_pattern(item.listing_url),
                depth=3,
                parent_page_key=brand_keys.get((item.section, item.brand_slug)),
                page_type="model_hub",
                section=item.section,
                title=item.label,
                excerpt=None,
                status=SiteNodeStatus.CRAWLED.value,
                content_hash=None,
                job_id=job_id,
                meta={"source": "taxonomy_sitemap", "brand_slug": item.brand_slug},
            )
        self._session.flush()


def _is_taxonomy_sitemap(url: str) -> bool:
    lowered = url.lower()
    if "-filter" in lowered:
        return False
    return any(f"/sitemap/{section}" in lowered for section in ("car", "motorcycle", "truck"))
