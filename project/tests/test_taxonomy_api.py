import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_current_user, get_db
from app.api.main import app
from app.db.base import Base
from app.models.site_map import SiteNode
from app.models.user import User
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
    session.add(User(id=1, email="test@example.com", password_hash="hash"))
    session.commit()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    def override_db():
        yield db_session

    def override_user():
        return db_session.get(User, 1)

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_user
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _seed_taxonomy(session):
    config = load_bama_site_config()
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
    TaxonomyBuilder(session, config, job_id="job-1").build()
    session.commit()


def test_taxonomy_brands_and_models(client, db_session):
    _seed_taxonomy(db_session)

    brands = client.get("/api/taxonomy/brands", params={"section": "car"})
    assert brands.status_code == 200
    data = brands.json()
    assert len(data) == 1
    assert data[0]["label"] == "پورشه"
    brand_id = data[0]["id"]

    models = client.get("/api/taxonomy/models", params={"section": "car", "brand_id": brand_id})
    assert models.status_code == 200
    model_data = models.json()
    assert len(model_data) == 1
    assert model_data[0]["label"] == "پانامرا"
    assert model_data[0]["listing_url"] == "https://bama.ir/car/porsche/panamera"


def test_taxonomy_sections(client, db_session):
    _seed_taxonomy(db_session)
    response = client.get("/api/taxonomy/sections")
    assert response.status_code == 200
    sections = {s["section_key"]: s for s in response.json()}
    assert sections["car"]["brand_count"] == 1
    assert sections["car"]["model_count"] == 1


def test_taxonomy_harvest_endpoint(client, db_session, monkeypatch):
    def fake_refresh(_db):
        return {"brands": 12, "models": 40, "snapshot_id": 3}

    monkeypatch.setattr("app.api.routes.taxonomy.refresh_taxonomy_catalog", fake_refresh)
    response = client.post("/api/taxonomy/harvest")
    assert response.status_code == 200
    body = response.json()
    assert body["brands"] == 12
    assert body["models"] == 40
    assert body["snapshot_id"] == 3
