from __future__ import annotations

from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.models.site_map import SiteNode
from app.repositories.site_node_repository import SiteNodeRepository
from app.repositories.taxonomy_repository import TaxonomyRepository
from config.bama_site import BamaSiteConfig

VEHICLE_SECTIONS = ("car", "motorcycle", "truck")
_BRAND_PAGE_TYPES = frozenset({"brand_hub", "hub", "listing", "model_hub", "section_hub"})
_MODEL_PAGE_TYPES = frozenset({"model_hub", "hub", "listing", "brand_hub"})


def _path_parts(url: str) -> list[str]:
    return [p for p in urlparse(url).path.split("/") if p]


def _canonical_listing_url(section: str, *segments: str) -> str:
    return f"https://bama.ir/{section}/{'/'.join(segments)}"


def _label_from_node(node: SiteNode, slug: str) -> str:
    if node.title and node.title.strip():
        return node.title.strip()
    return slug.replace("-", " ")


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
        brands_by_page_key: dict[str, int] = {}

        for section in VEHICLE_SECTIONS:
            nodes = self._nodes.list_all(section=section, limit=100_000)
            for node in nodes:
                if not _is_brand_node(node, section):
                    continue
                parts = _path_parts(node.url)
                slug = parts[1]
                term = self._taxonomy.add_term(
                    snapshot_id=snapshot.id,
                    section_key=section,
                    term_type="brand",
                    label=_label_from_node(node, slug),
                    slug=slug,
                    listing_url=_canonical_listing_url(section, slug),
                    page_key=node.page_key,
                    meta={
                        "depth": node.depth,
                        "page_type": node.page_type,
                        "path_parts": parts,
                    },
                )
                self._taxonomy.add_ref(
                    term_id=term.id,
                    page_key=node.page_key,
                    url=node.url,
                    url_pattern=node.url_pattern,
                    source_job_id=self._job_id,
                )
                brands_by_page_key[node.page_key] = term.id
                brand_count += 1

            for node in nodes:
                if not _is_model_node(node, section):
                    continue
                parts = _path_parts(node.url)
                if len(parts) < 3:
                    continue
                brand_slug, model_slug = parts[1], parts[2]
                parent_id = brands_by_page_key.get(node.parent_page_key or "")
                if parent_id is None:
                    brand_term = self._taxonomy.find_term_by_slug(
                        section_key=section,
                        term_type="brand",
                        slug=brand_slug,
                    )
                    parent_id = brand_term.id if brand_term else None
                term = self._taxonomy.add_term(
                    snapshot_id=snapshot.id,
                    section_key=section,
                    term_type="model",
                    label=_label_from_node(node, model_slug),
                    slug=model_slug,
                    listing_url=_canonical_listing_url(section, brand_slug, model_slug),
                    page_key=node.page_key,
                    parent_id=parent_id,
                    meta={
                        "depth": node.depth,
                        "page_type": node.page_type,
                        "path_parts": parts,
                        "brand_slug": brand_slug,
                    },
                )
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


def _is_brand_node(node: SiteNode, section: str) -> bool:
    if node.section != section or node.depth != 2:
        return False
    parts = _path_parts(node.url)
    if len(parts) != 2 or parts[0] != section:
        return False
    if node.page_type not in _BRAND_PAGE_TYPES:
        return False
    if "detail" in parts[1]:
        return False
    return True


def _is_model_node(node: SiteNode, section: str) -> bool:
    if node.section != section or node.depth != 3:
        return False
    parts = _path_parts(node.url)
    if len(parts) != 3 or parts[0] != section:
        return False
    if node.page_type not in _MODEL_PAGE_TYPES:
        return False
    if "detail" in parts[2]:
        return False
    return True
