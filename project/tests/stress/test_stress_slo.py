"""Consolidated stress SLO test — collects and asserts all metrics."""

from __future__ import annotations

import random

import pytest

from tests.stress.conftest import run_burst_measured, seed_advertisements
from tests.stress.thresholds import assert_within_thresholds

pytestmark = pytest.mark.stress


def test_stress_slo_full_metrics_report(
    stress_client,
    stress_db_session,
    stress_scale,
    mock_crawl_dispatch,
    db_instrument,
    redis_instrument,
    system_sampler,
    stress_session_report,
):
    """Single comprehensive burst with RPS, percentiles, CPU, DB, Redis metrics."""
    seed_advertisements(stress_db_session, min(stress_scale.ads, 300))

    endpoints = [
        "/api/health/live",
        "/api/metrics",
        "/api/ads",
        "/api/searches",
        "/api/notifications/unread-count",
        "/api/taxonomy/sections",
    ]

    def hit(i: int) -> tuple[int, str]:
        path = endpoints[i % len(endpoints)]
        if path == "/api/ads":
            response = stress_client.get(path, params={"limit": 20})
        else:
            response = stress_client.get(path)
        return response.status_code, path

    metrics = run_burst_measured(
        "slo_full_burst",
        stress_scale.api_requests,
        hit,
        db_instrument=db_instrument,
        redis_instrument=redis_instrument,
        system_sampler=system_sampler,
        session_report=stress_session_report,
    )

    assert metrics.request_count == stress_scale.api_requests
    assert metrics.rps > 0
    assert metrics.p50_ms >= 0
    assert metrics.p95_ms >= metrics.p50_ms
    assert metrics.p99_ms >= metrics.p95_ms
    assert metrics.error_rate < 0.5
    assert metrics.db_query_count > 0
    assert metrics.throughput_bytes_per_sec >= 0

    assert_within_thresholds(metrics)

    print("\n" + metrics.format_report())


def test_stress_preview_write_load_metrics(
    stress_client,
    stress_db_session,
    stress_scale,
    mock_crawl_dispatch,
    db_instrument,
    system_sampler,
    stress_session_report,
):
    seed_advertisements(stress_db_session, 100)
    brands = ["Toyota", "Honda", "BMW", "Renault"]

    def hit(i: int) -> tuple[int, str]:
        if i % 4 == 0:
            response = stress_client.post(
                "/api/ads/preview",
                json={"brand": brands[i % len(brands)], "limit": 20},
            )
            return response.status_code, "/api/ads/preview"
        response = stress_client.get("/api/ads", params={"limit": 30})
        return response.status_code, "/api/ads"

    metrics = run_burst_measured(
        "slo_preview_mix",
        min(stress_scale.api_requests, 150),
        hit,
        db_instrument=db_instrument,
        system_sampler=system_sampler,
        session_report=stress_session_report,
    )

    assert metrics.error_rate == 0.0
    assert metrics.db_queries_per_request > 0
    assert_within_thresholds(metrics)
