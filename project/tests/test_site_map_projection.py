from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.site_map import SiteNode
from app.repositories.site_section_repository import SiteSectionRepository
from config.bama_site import load_bama_site_config
from crawler.application.site_catalog_builder import SiteCatalogBuilder
from crawler.application.site_map_projection_builder import SiteMapProjectionBuilder


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
    url_pattern: str,
    depth: int,
    page_type: str,
    section: str,
) -> None:
    session.add(
        SiteNode(
            page_key=page_key,
            url=url,
            url_pattern=url_pattern,
            depth=depth,
            page_type=page_type,
            section=section,
            title=None,
            status="crawled",
        )
    )


def test_projection_aggregates_duplicate_patterns(db_session):
    config = load_bama_site_config()
    for i in range(10):
        _add_node(
            db_session,
            page_key=f"detail-{i}",
            url=f"https://bama.ir/car/toyota/detail-abc{i}",
            url_pattern="https://bama.ir/car/{brand}/detail-{id}",
            depth=3,
            page_type="ad_detail",
            section="car",
        )
    _add_node(
        db_session,
        page_key="hub-toyota",
        url="https://bama.ir/car/toyota",
        url_pattern="https://bama.ir/car/{brand}",
        depth=2,
        page_type="model_hub",
        section="car",
    )
    db_session.commit()

    SiteCatalogBuilder(db_session, config).build()
    summary = SiteMapProjectionBuilder(db_session, config).build()
    db_session.commit()

    from app.repositories.site_map_group_repository import SiteMapGroupRepository

    groups = SiteMapGroupRepository(db_session).list_all()
    pattern_groups = [g for g in groups if g.group_kind == "pattern_cluster"]
    detail_group = next(
        g for g in pattern_groups if g.page_count == 10 and g.url_pattern and "detail" in g.url_pattern
    )
    assert detail_group.page_count == 10
    assert detail_group.parent_group_key == "section:car"
    assert detail_group.representative_page_key is not None
    assert detail_group.weight >= 1
    hub_groups = [g for g in groups if g.group_kind == "path_hub"]
    assert any("other_hubs" in g.group_key for g in hub_groups)
    assert len(groups) < 15
