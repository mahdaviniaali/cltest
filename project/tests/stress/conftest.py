"""Shared fixtures for stress tests — network guard + seeded DB/API client + metrics."""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, TypeVar
from unittest.mock import patch
from urllib.parse import urlparse

import pytest
import requests
import time
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_current_user, get_db
from app.api.main import app
from app.db.base import Base
from app.models.advertisement import Advertisement
from app.models.user import User
from crawler.core import http_client
from tests.stress.instrumentation import DbQueryInstrument, RedisInstrument, SystemSampler
from tests.stress.metrics import StressRunMetrics, StressSessionReport
from tests.stress.scale import StressScale, get_stress_scale

T = TypeVar("T")

_BLOCKED_HOSTS = {"bama.ir", "www.bama.ir"}
_SESSION_REPORT = StressSessionReport()


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "stress: heavy load/stress tests")


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    if not _SESSION_REPORT.runs:
        return
    print("\n" + _SESSION_REPORT.format_summary())
    if os.getenv("STRESS_REPORT_JSON", "0") == "1":
        report_dir = Path(__file__).resolve().parent / "reports"
        path = report_dir / "session_metrics.json"
        _SESSION_REPORT.write_json(path)
        print(f"\nStress metrics JSON: {path}")


def _assert_not_bama(url: str) -> None:
    host = (urlparse(url).hostname or "").lower()
    if host in _BLOCKED_HOSTS or host.endswith(".bama.ir"):
        pytest.fail(f"Stress test attempted live fetch to Bama: {url}")


def _import_all_models() -> None:
    import app.models.advertisement  # noqa: F401
    import app.models.crawl_job  # noqa: F401
    import app.models.crawler_state  # noqa: F401
    import app.models.filter_crawl_state  # noqa: F401
    import app.models.match  # noqa: F401
    import app.models.notification  # noqa: F401
    import app.models.outbox_event  # noqa: F401
    import app.models.search  # noqa: F401
    import app.models.site_map  # noqa: F401
    import app.models.taxonomy  # noqa: F401
    import app.models.user  # noqa: F401


@pytest.fixture(autouse=True)
def block_bama_network():
    """Fail immediately if any code tries to hit bama.ir over the network."""
    original_http_get = http_client.HttpClient.get
    original_session_get = requests.Session.get

    def guarded_http_get(self, url: str, *args, **kwargs):
        _assert_not_bama(url)
        return original_http_get(self, url, *args, **kwargs)

    def guarded_session_get(self, url: str, *args, **kwargs):
        _assert_not_bama(url)
        return original_session_get(self, url, *args, **kwargs)

    with (
        patch.object(http_client.HttpClient, "get", guarded_http_get),
        patch.object(requests.Session, "get", guarded_session_get),
    ):
        yield


@pytest.fixture()
def stress_scale() -> StressScale:
    return get_stress_scale()


@pytest.fixture()
def stress_session_report() -> StressSessionReport:
    return _SESSION_REPORT


@pytest.fixture()
def db_instrument():
    instrument = DbQueryInstrument()
    yield instrument
    instrument.reset()


@pytest.fixture()
def redis_instrument():
    instrument = RedisInstrument()
    with instrument.patch_redis(use_mock=True):
        yield instrument
    instrument.reset()


@pytest.fixture()
def system_sampler() -> SystemSampler:
    return SystemSampler()


@pytest.fixture()
def stress_db_session(db_instrument):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    db_instrument.attach(engine)
    _import_all_models()
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    session = SessionLocal()
    user = User(id=1, email="stress@example.com", password_hash="hash", full_name="Stress")
    session.add(user)
    session.commit()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def stress_client(stress_db_session: Session):
    def override_db():
        yield stress_db_session

    def override_user():
        return stress_db_session.get(User, 1)

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_user
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture()
def mock_crawl_dispatch():
    """Prevent Celery/thread crawl dispatch during API stress tests."""
    with (
        patch("app.api.routes.searches.dispatch_on_demand_job") as search_dispatch,
        patch("app.api.routes.crawl.dispatch_on_demand_job") as crawl_dispatch,
        patch("app.api.routes.inspector.dispatch_site_map_job") as site_map_dispatch,
    ):
        yield {
            "search": search_dispatch,
            "crawl": crawl_dispatch,
            "site_map": site_map_dispatch,
        }


def seed_advertisements(session: Session, count: int, *, brand: str = "Toyota") -> list[Advertisement]:
    now = datetime.now(timezone.utc)
    ads: list[Advertisement] = []
    for i in range(count):
        ad = Advertisement(
            bama_id=f"seed-{i:06d}",
            url=f"https://bama.ir/car/detail-seed-{i:06d}",
            title=f"{brand} Camry {i}",
            brand=brand,
            model="Camry",
            year=1400 + (i % 5),
            price=1_000_000_000 + i * 10_000,
            mileage=50_000 + i * 100,
            location="تهران",
            crawled_at=now,
        )
        ads.append(ad)
    session.add_all(ads)
    session.commit()
    return ads


def run_burst(total_tasks: int, task_fn: Callable[[int], T]) -> list[T]:
    """Sequential burst — safe with shared SQLite session + TestClient."""
    return [task_fn(i) for i in range(total_tasks)]


def run_burst_measured(
    name: str,
    total_tasks: int,
    task_fn: Callable[[int], tuple[int, str]],
    *,
    db_instrument: DbQueryInstrument | None = None,
    redis_instrument: RedisInstrument | None = None,
    system_sampler: SystemSampler | None = None,
    session_report: StressSessionReport | None = None,
) -> StressRunMetrics:
    """Run burst and collect RPS, percentiles, DB/Redis/CPU metrics."""
    metrics = StressRunMetrics(name=name)
    sampler = system_sampler or SystemSampler()

    if db_instrument is not None:
        db_instrument.reset()
    if redis_instrument is not None:
        redis_instrument.reset()

    with sampler.sample():
        for i in range(total_tasks):
            start = time.perf_counter()
            status_code, endpoint = task_fn(i)
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            metrics.record_request(
                latency_ms=elapsed_ms,
                status_code=status_code,
                endpoint=endpoint,
                bytes_received=len(str(status_code)),
            )
            metrics.network_latency_ms.append(elapsed_ms)

    metrics.finish()

    if db_instrument is not None:
        db_instrument.sync_to(metrics)
    if redis_instrument is not None:
        redis_instrument.sync_to(metrics)
    sampler.sync_to(metrics)

    if session_report is not None:
        session_report.add(metrics)

    return metrics


def run_concurrent(
    workers: int,
    total_tasks: int,
    task_fn: Callable[[int], T],
) -> list[T]:
    results: list[T] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(task_fn, i) for i in range(total_tasks)]
        for future in as_completed(futures):
            results.append(future.result())
    return results


def assert_no_server_errors(status_codes: list[int]) -> None:
    server_errors = [code for code in status_codes if code >= 500]
    assert not server_errors, f"Unexpected 5xx responses: {server_errors[:10]} (total {len(server_errors)})"
