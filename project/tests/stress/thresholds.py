"""SLO thresholds for stress runs — override via env vars."""

from __future__ import annotations

import os
from dataclasses import dataclass

from tests.stress.metrics import StressRunMetrics


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    return float(raw)


@dataclass(frozen=True, slots=True)
class StressThresholds:
    max_error_rate: float = 0.01
    max_p99_ms: float = 5000.0
    max_db_latency_p99_ms: float = 500.0
    max_db_queries_per_request: float = 50.0
    min_rps: float = 1.0
    max_cpu_percent: float = 95.0
    max_memory_mb: float = 2048.0
    min_redis_hit_rate: float = 0.0

    @classmethod
    def from_env(cls) -> "StressThresholds":
        return cls(
            max_error_rate=_env_float("STRESS_MAX_ERROR_RATE", 0.01),
            max_p99_ms=_env_float("STRESS_MAX_P99_MS", 5000.0),
            max_db_latency_p99_ms=_env_float("STRESS_MAX_DB_P99_MS", 500.0),
            max_db_queries_per_request=_env_float("STRESS_MAX_DB_QPR", 50.0),
            min_rps=_env_float("STRESS_MIN_RPS", 1.0),
            max_cpu_percent=_env_float("STRESS_MAX_CPU_PCT", 95.0),
            max_memory_mb=_env_float("STRESS_MAX_MEMORY_MB", 2048.0),
            min_redis_hit_rate=_env_float("STRESS_MIN_REDIS_HIT_RATE", 0.0),
        )


def assert_within_thresholds(metrics: StressRunMetrics, thresholds: StressThresholds | None = None) -> None:
    """Assert metrics meet SLO thresholds; raises AssertionError with details."""
    t = thresholds or StressThresholds.from_env()
    violations: list[str] = []

    if metrics.error_rate > t.max_error_rate:
        violations.append(f"error_rate {metrics.error_rate:.4f} > {t.max_error_rate}")
    if metrics.p99_ms > t.max_p99_ms:
        violations.append(f"p99_ms {metrics.p99_ms:.1f} > {t.max_p99_ms}")
    if metrics.db_latency_p99_ms > t.max_db_latency_p99_ms and metrics.db_query_count > 0:
        violations.append(f"db_p99_ms {metrics.db_latency_p99_ms:.1f} > {t.max_db_latency_p99_ms}")
    if metrics.db_queries_per_request > t.max_db_queries_per_request and metrics.request_count > 0:
        violations.append(
            f"db_queries_per_request {metrics.db_queries_per_request:.1f} > {t.max_db_queries_per_request}"
        )
    if metrics.rps < t.min_rps and metrics.request_count > 10:
        violations.append(f"rps {metrics.rps:.1f} < {t.min_rps}")
    if metrics.cpu_percent_avg is not None and metrics.cpu_percent_avg > t.max_cpu_percent:
        violations.append(f"cpu_percent {metrics.cpu_percent_avg:.1f} > {t.max_cpu_percent}")
    if metrics.memory_mb_peak is not None and metrics.memory_mb_peak > t.max_memory_mb:
        violations.append(f"memory_mb {metrics.memory_mb_peak:.1f} > {t.max_memory_mb}")
    hit_rate = metrics.redis_hit_rate
    if hit_rate is not None and metrics.redis_ops > 0 and hit_rate < t.min_redis_hit_rate:
        violations.append(f"redis_hit_rate {hit_rate:.4f} < {t.min_redis_hit_rate}")

    if violations:
        report = metrics.format_report()
        raise AssertionError("Stress SLO violations:\n  - " + "\n  - ".join(violations) + f"\n\n{report}")
