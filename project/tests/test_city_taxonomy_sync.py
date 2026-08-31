from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.advertisement import Advertisement
from app.services.city_taxonomy_sync import CityTaxonomySync


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


def test_city_taxonomy_sync_from_ads(db_session):
    db_session.add(
        Advertisement(
            bama_id="ad-1",
            url="https://bama.ir/car/detail-1",
            title="test",
            location="تهران",
        )
    )
    db_session.add(
        Advertisement(
            bama_id="ad-2",
            url="https://bama.ir/car/detail-2",
            title="test2",
            location="اصفهان",
        )
    )
    db_session.commit()

    added = CityTaxonomySync(db_session).sync()
    db_session.commit()
    assert added >= 2

    cities = CityTaxonomySync(db_session).list_cities(section_key="car")
    assert "تهران" in cities
    assert "اصفهان" in cities
