"""Locust metrics reporter — RPS, percentiles, error rate, CPU, memory, throughput."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(PROJECT_DIR / "src"))

from locust import events

from tests.stress.instrumentation import SystemSampler
from tests.stress.metrics import StressRunMetrics
from tests.stress.thresholds import StressThresholds, assert_within_thresholds

_SAMPLER = SystemSampler()
_START_TIME: float = 0.0
_REPORT_PATH = Path(__file__).resolve().parent / "reports" / "locust_metrics.json"


@events.test_start.add_listener
def _on_test_start(environment, **kwargs) -> None:
    global _START_TIME
    _START_TIME = time.perf_counter()
    _SAMPLER.cpu_samples.clear()
    _SAMPLER.memory_mb_samples.clear()
    _SAMPLER.start()


@events.test_stop.add_listener
def _on_test_stop(environment, **kwargs) -> None:
    _SAMPLER.stop()
    duration = max(time.perf_counter() - _START_TIME, 1e-9)
    total = environment.stats.total

    metrics = StressRunMetrics(name="locust_run")
    metrics.started_at = _START_TIME
    metrics.ended_at = time.perf_counter()

    for _ in range(total.num_requests):
        metrics.record_request(
            latency_ms=total.avg_response_time or 0.0,
            status_code=200,
        )

    metrics.requests.clear()
    for entry in environment.stats.entries.values():
        for _ in range(entry.num_requests):
            metrics.record_request(
                latency_ms=entry.avg_response_time or 0.0,
                status_code=500 if entry.num_failures else 200,
                endpoint=entry.name,
            )

    if not metrics.requests and total.num_requests:
        metrics.record_request(
            latency_ms=total.avg_response_time or 0.0,
            status_code=200 if not total.num_failures else 500,
            endpoint="aggregate",
        )

    _SAMPLER.sync_to(metrics)

    report = {
        **metrics.to_dict(),
        "locust": {
            "num_requests": total.num_requests,
            "num_failures": total.num_failures,
            "avg_response_time_ms": total.avg_response_time,
            "min_response_time_ms": total.min_response_time,
            "max_response_time_ms": total.max_response_time,
            "current_rps": total.current_rps,
            "p50_ms": total.get_response_time_percentile(0.5),
            "p95_ms": total.get_response_time_percentile(0.95),
            "p99_ms": total.get_response_time_percentile(0.99),
        },
        "db_query_count": None,
        "db_latency_p99_ms": None,
        "redis_hit_rate": None,
        "note": "DB/Redis metrics require server-side instrumentation; use pytest -m stress for in-process DB tracking.",
    }

    report["error_rate"] = (
        total.num_failures / total.num_requests if total.num_requests else 0.0
    )
    report["rps"] = round(total.num_requests / duration, 2)
    report["network_latency_p50_ms"] = report["locust"]["p50_ms"]
    report["network_latency_p95_ms"] = report["locust"]["p95_ms"]
    report["network_latency_p99_ms"] = report["locust"]["p99_ms"]

    print("\n=== Locust stress metrics ===")
    for key in (
        "rps",
        "error_rate",
        "p50_ms",
        "p95_ms",
        "p99_ms",
        "cpu_percent_avg",
        "memory_mb_peak",
        "throughput_bytes_per_sec",
    ):
        print(f"  {key}: {report.get(key, report['locust'].get(key))}")

    if os.getenv("STRESS_REPORT_JSON", "1") == "1":
        _REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        _REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"\nLocust metrics JSON: {_REPORT_PATH}")

    if os.getenv("STRESS_ASSERT_SLO", "0") == "1":
        slo_metrics = StressRunMetrics(name="locust_slo")
        slo_metrics.requests = metrics.requests
        slo_metrics.ended_at = metrics.ended_at
        slo_metrics.started_at = metrics.started_at
        slo_metrics.cpu_percent_samples = metrics.cpu_percent_samples
        slo_metrics.memory_mb_samples = metrics.memory_mb_samples
        assert_within_thresholds(slo_metrics, StressThresholds.from_env())
