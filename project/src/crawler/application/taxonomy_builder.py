from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.site_map import SiteNode
from app.repositories.site_node_repository import SiteNodeRepository
from app.repositories.taxonomy_repository import TaxonomyRepository
from config.bama_site import BamaSiteConfig
from crawler.domain.taxonomy_urls import VEHICLE_SECTIONS, classify_taxonomy_urls

# Re-exported for existing importers (city taxonomy sync, tests).
__all__ = ["TaxonomyBuilder", "VEHICLE_SECTIONS"]


class TaxonomyBuilder:
    def __init__(
        self,
        session: Session,
        config: BamaSiteConfig,
        *,
        job_id: str | None = None,
    ) -> None:
        self._session = session
        self._config = config
        self._job_id = job_id
        self._nodes = SiteNodeRepository(session)
        self._taxonomy = TaxonomyRepository(session)

    def build(self) -> dict:
        snapshot = self._taxonomy.create_snapshot(source_job_id=self._job_id)
        brand_count = 0
        model_count = 0
        brands_by_listing: dict[str, int] = {}
        brands_by_section_slug: dict[tuple[str, str], int] = {}

        nodes_by_section: dict[str, list[SiteNode]] = {section: [] for section in VEHICLE_SECTIONS}
        for section in VEHICLE_SECTIONS:
            nodes_by_section[section] = self._nodes.list_all(section=section, limit=100_000)

        for section in VEHICLE_SECTIONS:
            nodes = nodes_by_section[section]
            classified = classify_taxonomy_urls([node.url for node in nodes])
            node_by_url = {_node_listing_url(node): node for node in nodes}

            for item in classified:
                if item.term_type != "brand":
                    continue
                node = node_by_url.get(item.listing_url)
                term = self._taxonomy.add_term(
                    snapshot_id=snapshot.id,
                    section_key=section,
                    term_type="brand",
                    label=_label_for(node, item.label),
                    slug=item.slug,
                    listing_url=item.listing_url,
                    page_key=node.page_key if node else None,
                    meta={
                        "depth": node.depth if node else 2,
                        "page_type": node.page_type if node else "brand_hub",
                        "path_parts": [section, item.slug],
                    },
                )
                if node is not None:
                    self._taxonomy.add_ref(
                        term_id=term.id,
                        page_key=node.page_key,
                        url=node.url,
                        url_pattern=node.url_pattern,
                        source_job_id=self._job_id,
                    )
                brands_by_listing[item.listing_url] = term.id
                brands_by_section_slug[(section, item.slug)] = term.id
                brand_count += 1

            for item in classified:
                if item.term_type != "model":
                    continue
                node = node_by_url.get(item.listing_url)
                parent_id = None
                if item.parent_listing_url:
                    parent_id = brands_by_listing.get(item.parent_listing_url)
                if parent_id is None:
                    parent_id = brands_by_section_slug.get((section, item.brand_slug))
                term = self._taxonomy.add_term(
                    snapshot_id=snapshot.id,
                    section_key=section,
                    term_type="model",
                    label=_label_for(node, item.label),
                    slug=item.slug,
                    listing_url=item.listing_url,
                    page_key=node.page_key if node else None,
                    parent_id=parent_id,
                    meta={
                        "depth": node.depth if node else 3,
                        "page_type": node.page_type if node else "model_hub",
                        "path_parts": [section, item.brand_slug, item.slug],
                        "brand_slug": item.brand_slug,
                    },
                )
                if node is not None:
                    self._taxonomy.add_ref(
                        term_id=term.id,
                        page_key=node.page_key,
                        url=node.url,
                        url_pattern=node.url_pattern,
                        source_job_id=self._job_id,
                    )
                model_count += 1

        self._session.flush()
        return {
            "snapshot_id": snapshot.id,
            "brands": brand_count,
            "models": model_count,
        }


def _node_listing_url(node: SiteNode) -> str:
    return node.url.split("?")[0].rstrip("/")


def _label_for(node: SiteNode | None, fallback: str) -> str:
    if node is not None and node.title and node.title.strip():
        return node.title.strip()
    return fallback
