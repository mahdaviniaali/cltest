from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.search import Search
from app.models.site_map import SiteNode
from app.models.user import User
from config.bama_site import load_bama_site_config
from crawler.application.search_listing_url_builder import build_search_listing_url
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
    session.add(User(id=1, email="test@example.com", password_hash="hash"))
    session.commit()
    try:
        yield session
    finally:
        session.close()


def _seed_porsche_panamera(session):
    session.add(
        SiteNode(
            page_key="brand-porsche",
            url="https://bama.ir/car/porsche",
            url_pattern="https://bama.ir/car/{brand}",
            depth=2,
            page_type="brand_hub",
            section="car",
            title="پورشه",
            status="crawled",
        )
    )
    session.add(
        SiteNode(
            page_key="model-panamera",
            url="https://bama.ir/car/porsche/panamera",
            url_pattern="https://bama.ir/car/{brand}/{model}",
            depth=3,
            parent_page_key="brand-porsche",
            page_type="model_hub",
            section="car",
            title="پانامرا",
            status="crawled",
        )
    )
    session.commit()
    TaxonomyBuilder(session, load_bama_site_config(), job_id="job-1").build()
    session.commit()


def test_listing_url_from_taxonomy_porsche_panamera(db_session):
    _seed_porsche_panamera(db_session)
    search = Search(
        user_id=1,
        brand="پورش",
        model="پانامرا",
        enabled=True,
    )
    url = build_search_listing_url(db_session, search)
    assert url == "https://bama.ir/car/porsche/panamera"


def test_listing_url_from_term_ids(db_session):
    _seed_porsche_panamera(db_session)
    from app.repositories.taxonomy_repository import TaxonomyRepository

    repo = TaxonomyRepository(db_session)
    brand = repo.find_term_by_slug(section_key="car", term_type="brand", slug="porsche")
    model = repo.list_terms(section_key="car", term_type="model", parent_id=brand.id)[0]
    search = Search(user_id=1, brand="پورشه", model="پانامرا", enabled=True)
    search.brand_term_id = brand.id
    search.model_term_id = model.id
    url = build_search_listing_url(db_session, search)
    assert url == "https://bama.ir/car/porsche/panamera"
