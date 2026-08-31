"""API storm stress tests — hammer our FastAPI, not Bama."""

from __future__ import annotations

import random
from datetime import datetime, timezone

import pytest

from app.models.crawl_job import CrawlJob, CrawlJobStatus, CrawlJobType
from app.models.search import Search

from tests.stress.conftest import (
    assert_no_server_errors,
    run_burst_measured,
    seed_advertisements,
)
from tests.stress.thresholds import assert_within_thresholds

pytestmark = pytest.mark.stress


def test_health_and_metrics_under_burst(
    stress_client,
    stress_scale,
    db_instrument,
    system_sampler,
    stress_session_report,
):
    endpoints = [
        "/api/health/live",
        "/api/health",
        "/api/metrics",
    ]

    def hit(i: int) -> tuple[int, str]:
        path = random.choice(endpoints)
        return stress_client.get(path).status_code, path

    metrics = run_burst_measured(
        "health_metrics_burst",
        stress_scale.api_requests,
        hit,
        db_instrument=db_instrument,
        system_sampler=system_sampler,
        session_report=stress_session_report,
    )
    assert_no_server_errors([r.status_code for r in metrics.requests])
    assert all(r.status_code in (200, 503) for r in metrics.requests)
    assert_within_thresholds(metrics)


def test_ads_list_and_preview_storm(
    stress_client,
    stress_db_session,
    stress_scale,
    mock_crawl_dispatch,
    db_instrument,
    system_sampler,
    stress_session_report,
):
    seed_advertisements(stress_db_session, stress_scale.ads)

    def hit(i: int) -> tuple[int, str]:
        if i % 3 == 0:
            response = stress_client.get("/api/ads", params={"limit": 50, "offset": i % 100})
            return response.status_code, "/api/ads"
        response = stress_client.post(
            "/api/ads/preview",
            json={"brand": "Toyota", "limit": 20},
        )
        return response.status_code, "/api/ads/preview"

    metrics = run_burst_measured(
        "ads_preview_burst",
        stress_scale.api_requests,
        hit,
        db_instrument=db_instrument,
        system_sampler=system_sampler,
        session_report=stress_session_report,
    )
    assert_no_server_errors([r.status_code for r in metrics.requests])
    assert all(r.status_code == 200 for r in metrics.requests)
    assert metrics.db_query_count > 0
    assert_within_thresholds(metrics)


def test_search_results_storm(
    stress_client,
    stress_db_session,
    stress_scale,
    mock_crawl_dispatch,
    db_instrument,
    system_sampler,
    stress_session_report,
):
    seed_advertisements(stress_db_session, min(stress_scale.ads, 200), brand="Honda")
    search = Search(user_id=1, brand="Honda", enabled=True)
    stress_db_session.add(search)
    stress_db_session.commit()
    stress_db_session.refresh(search)

    search_id = search.id

    def hit(_: int) -> tuple[int, str]:
        response = stress_client.get(f"/api/searches/{search_id}/results")
        return response.status_code, "/api/searches/results"

    metrics = run_burst_measured(
        "search_results_burst",
        stress_scale.api_requests,
        hit,
        db_instrument=db_instrument,
        system_sampler=system_sampler,
        session_report=stress_session_report,
    )
    assert_no_server_errors([r.status_code for r in metrics.requests])
    assert all(r.status_code == 200 for r in metrics.requests)
    assert_within_thresholds(metrics)


def test_refresh_stampede_no_duplicate_dispatch(
    stress_client,
    stress_db_session,
    stress_scale,
    mock_crawl_dispatch,
    db_instrument,
    system_sampler,
    stress_session_report,
):
    stress_db_session.add(
        CrawlJob(
            id="running-stampede",
            job_type=CrawlJobType.ON_DEMAND_GLOBAL.value,
            status=CrawlJobStatus.RUNNING.value,
            triggered_by="stress",
            idempotency_key="stampede:running",
            started_at=datetime.now(timezone.utc),
        )
    )
    stress_db_session.commit()

    def refresh(_: int) -> tuple[int, str]:
        response = stress_client.post("/api/crawl/refresh")
        return response.status_code, "/api/crawl/refresh"

    metrics = run_burst_measured(
        "refresh_stampede",
        50,
        refresh,
        db_instrument=db_instrument,
        system_sampler=system_sampler,
        session_report=stress_session_report,
    )
    assert_no_server_errors([r.status_code for r in metrics.requests])
    assert all(r.status_code == 202 for r in metrics.requests)
    mock_crawl_dispatch["crawl"].assert_not_called()
    assert_within_thresholds(metrics)


def test_taxonomy_and_inspector_read_storm(
    stress_client,
    stress_db_session,
    stress_scale,
    mock_crawl_dispatch,
    db_instrument,
    system_sampler,
    stress_session_report,
):
    seed_advertisements(stress_db_session, 50, brand="Toyota")

    paths = [
        "/api/taxonomy/sections",
        "/api/taxonomy/brands?section=car",
        "/api/inspector/jobs",
        "/api/inspector/site/tree",
        "/api/inspector/site/map",
        "/api/inspector/stats/overview",
        "/api/admin/stats",
    ]

    def hit(_: int) -> tuple[int, str]:
        path = random.choice(paths)
        return stress_client.get(path).status_code, path.split("?")[0]

    metrics = run_burst_measured(
        "taxonomy_inspector_burst",
        min(stress_scale.api_requests, 150),
        hit,
        db_instrument=db_instrument,
        system_sampler=system_sampler,
        session_report=stress_session_report,
    )
    assert_no_server_errors([r.status_code for r in metrics.requests])
    assert all(r.status_code == 200 for r in metrics.requests)
    assert_within_thresholds(metrics)
