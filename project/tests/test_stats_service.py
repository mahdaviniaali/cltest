from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.search import Search
from app.models.taxonomy import SearchBootstrapMetric
from app.models.user import User
from app.services.stats_service import StatsService


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


def test_stats_service_search_discovery_low_yield(db_session):
    search = Search(user_id=1, brand="پورشه", model="پانامرا", enabled=True)
    db_session.add(search)
    db_session.flush()
    db_session.add(
        SearchBootstrapMetric(
            search_id=search.id,
            job_id="job-1",
            listing_url="https://bama.ir/car/porsche/panamera",
            pages_crawled=2,
            ads_found=10,
            ads_new=3,
            matching_count=1,
        )
    )
    db_session.commit()

    rows = StatsService(db_session).get_search_discovery(threshold=5)
    assert len(rows) == 1
    assert rows[0].low_yield is True
    assert rows[0].listing_url == "https://bama.ir/car/porsche/panamera"


def test_stats_service_overview(db_session):
    overview = StatsService(db_session).get_overview()
    assert overview.crawl_health.total_jobs >= 0
    assert overview.taxonomy_active_brands >= 0
