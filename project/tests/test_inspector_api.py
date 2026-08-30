from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_current_user, get_db
from app.api.main import app
from app.db.base import Base
from app.models.crawl_job import CrawlJob, CrawlJobStatus, CrawlJobType
from app.models.site_map import SiteNode
from app.models.user import User


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


@patch("app.services.job_dispatch._broker_available", return_value=True)
@patch("app.workers.tasks.crawl.site_map_crawl")
def test_start_site_map_enqueues_job(mock_task, _broker, client, db_session):
    response = client.post("/api/inspector/site-map/start", json={"max_pages": 10, "max_depth": 2})
    assert response.status_code == 200
    data = response.json()
    assert data["job_type"] == CrawlJobType.SITE_MAP.value
    mock_task.delay.assert_called_once()


def test_start_site_map_idempotent_when_running(client, db_session):
    job_id = str(uuid4())
    db_session.add(
        CrawlJob(
            id=job_id,
            job_type=CrawlJobType.SITE_MAP.value,
            status=CrawlJobStatus.RUNNING.value,
            triggered_by="user:1",
            idempotency_key="existing",
            pages_crawled=5,
        )
    )
    db_session.commit()

    with patch("app.api.routes.inspector.dispatch_site_map_job") as mock_dispatch:
        response = client.post("/api/inspector/site-map/start", json={})
        assert response.status_code == 200
        assert response.json()["job_id"] == job_id
        mock_dispatch.assert_not_called()


def test_site_tree_and_graph(client, db_session):
    db_session.add(
        SiteNode(
            page_key="k1",
            url="https://bama.ir/car",
            url_pattern="https://bama.ir/car",
            depth=1,
            page_type="listing",
            section="car",
            title="Car",
            status="crawled",
        )
    )
    db_session.commit()

    tree = client.get("/api/inspector/site/tree")
    assert tree.status_code == 200
    assert len(tree.json()) >= 1

    graph = client.get("/api/inspector/site/graph")
    assert graph.status_code == 200
    assert len(graph.json()["nodes"]) == 1
