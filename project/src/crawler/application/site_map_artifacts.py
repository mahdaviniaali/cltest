from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories.site_node_repository import SiteNodeRepository
from config.bama_site import BamaSiteConfig
from crawler.application.site_catalog_builder import SiteCatalogBuilder
from crawler.application.site_map_projection_builder import SiteMapProjectionBuilder


def rebuild_site_map_artifacts(
    session: Session,
    config: BamaSiteConfig,
    *,
    job_id: str | None = None,
    include_taxonomy: bool = True,
) -> dict:
    """Rebuild Inspector catalog/map (and optionally taxonomy) from stored site_nodes.

    Partial crawls still persist nodes; the grouped map is derived, not crawled.
    """
    if SiteNodeRepository(session).count() == 0:
        return {"sections": [], "map_groups": 0, "taxonomy": None}

    sections = SiteCatalogBuilder(session, config).build()
    map_groups = SiteMapProjectionBuilder(session, config).build()
    taxonomy = None
    if include_taxonomy:
        from crawler.application.taxonomy_builder import TaxonomyBuilder

        taxonomy = TaxonomyBuilder(session, config, job_id=job_id).build()
    return {
        "sections": sections,
        "map_groups": len(map_groups),
        "taxonomy": taxonomy,
    }
