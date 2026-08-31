"""Redis health probe metrics — tracks hit rate via instrumented client."""

from __future__ import annotations

import pytest

from tests.stress.conftest import run_burst_measured
from tests.stress.thresholds import assert_within_thresholds

pytestmark = pytest.mark.stress


def test_redis_health_ready_hit_rate(
    stress_client,
    redis_instrument,
    system_sampler,
    stress_session_report,
):
    """Probe /api/health/ready with mocked Redis — validates hit-rate tracking."""

    def hit(_: int) -> tuple[int, str]:
        return stress_client.get("/api/health/ready").status_code, "/api/health/ready"

    metrics = run_burst_measured(
        "redis_ready_probe",
        30,
        hit,
        redis_instrument=redis_instrument,
        system_sampler=system_sampler,
        session_report=stress_session_report,
    )

    assert metrics.redis_ops >= 30
    assert metrics.redis_hit_rate == 1.0
    assert all(r.status_code == 200 for r in metrics.requests)
    assert_within_thresholds(metrics)
