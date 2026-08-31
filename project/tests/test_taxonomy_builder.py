from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.site_map import SiteNode
from app.repositories.taxonomy_repository import TaxonomyRepository
from config.bama_site import load_bama_site_config
from crawler.application.taxonomy_builder import TaxonomyBuilder


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    import app.models.advertisement  # noqa: F401
    import app.models.crawl_job  # noqa: F401
    import app.models.crawler_state  # noqa: F401
    import app.models.match  # noqa: F401
    import app.models.notification  # noqa: F401
    import app.models.outbox_event  # noqa: F401
    import app.models.search  # noqa: F401
    import app.models.site_map  # noqa: F401
    import app.models.taxonomy  # noqa: F401
    import app.models.user  # noqa: F401

    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def _add_node(
    session,
    *,
    page_key: str,
    url: str,
    depth: int,
    page_type: str,
    section: str,
    title: str | None = None,
    parent_page_key: str | None = None,
) -> None:
    session.add(
        SiteNode(
            page_key=page_key,
            url=url,
            url_pattern=url,
            depth=depth,
            parent_page_key=parent_page_key,
            page_type=page_type,
            section=section,
            title=title,
            status="crawled",
        )
    )


def test_taxonomy_builder_extracts_brands_and_models(db_session):
    config = load_bama_site_config()
    _add_node(
        db_session,
        page_key="brand-porsche",
        url="https://bama.ir/car/porsche",
        depth=2,
        page_type="brand_hub",
        section="car",
        title="پورشه",
    )
    _add_node(
        db_session,
        page_key="model-panamera",
        url="https://bama.ir/car/porsche/panamera",
        depth=3,
        page_type="model_hub",
        section="car",
        title="پانامرا",
        parent_page_key="brand-porsche",
    )
    db_session.commit()

    summary = TaxonomyBuilder(db_session, config, job_id="job-1").build()
    db_session.commit()

    assert summary["brands"] == 1
    assert summary["models"] == 1

    repo = TaxonomyRepository(db_session)
    brands = repo.list_terms(section_key="car", term_type="brand")
    models = repo.list_terms(section_key="car", term_type="model")
    assert len(brands) == 1
    assert brands[0].label == "پورشه"
    assert brands[0].listing_url == "https://bama.ir/car/porsche"
    assert len(models) == 1
    assert models[0].label == "پانامرا"
    assert models[0].listing_url == "https://bama.ir/car/porsche/panamera"
    assert models[0].parent_id == brands[0].id

    refs = repo.list_terms(section_key="car", term_type="brand")
    assert refs[0].page_key == "brand-porsche"


def test_taxonomy_builder_deactivates_stale_terms(db_session):
    config = load_bama_site_config()
    _add_node(
        db_session,
        page_key="brand-toyota",
        url="https://bama.ir/car/toyota",
        depth=2,
        page_type="brand_hub",
        section="car",
        title="تویوتا",
    )
    db_session.commit()
    TaxonomyBuilder(db_session, config, job_id="job-1").build()
    db_session.commit()

    _add_node(
        db_session,
        page_key="brand-bmw",
        url="https://bama.ir/car/bmw",
        depth=2,
        page_type="brand_hub",
        section="car",
        title="بی‌ام‌و",
    )
    db_session.query(SiteNode).filter(SiteNode.page_key == "brand-toyota").delete()
    db_session.commit()

    TaxonomyBuilder(db_session, config, job_id="job-2").build()
    db_session.commit()

    repo = TaxonomyRepository(db_session)
    active = repo.list_terms(section_key="car", term_type="brand")
    assert len(active) == 1
    assert active[0].slug == "bmw"
    assert repo.count_stale_terms(term_type="brand") == 1
