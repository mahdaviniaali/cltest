"""Stress run metrics — RPS, percentiles, resource and infra counters."""

from __future__ import annotations

import json
import statistics
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    ordered = sorted(values)
    rank = (pct / 100.0) * (len(ordered) - 1)
    low = int(rank)
    high = min(low + 1, len(ordered) - 1)
    weight = rank - low
    return ordered[low] * (1.0 - weight) + ordered[high] * weight


@dataclass(slots=True)
class RequestSample:
    latency_ms: float
    status_code: int
    endpoint: str = ""
    bytes_sent: int = 0
    bytes_received: int = 0


@dataclass
class StressRunMetrics:
    """Aggregated metrics for one stress burst or Locust run."""

    name: str
    started_at: float = field(default_factory=time.perf_counter)
    ended_at: float = 0.0
    requests: list[RequestSample] = field(default_factory=list)
    db_query_count: int = 0
    db_latency_ms: list[float] = field(default_factory=list)
    redis_ops: int = 0
    redis_hits: int = 0
    redis_misses: int = 0
    cpu_percent_samples: list[float] = field(default_factory=list)
    memory_mb_samples: list[float] = field(default_factory=list)
    network_latency_ms: list[float] = field(default_factory=list)

    def finish(self) -> None:
        self.ended_at = time.perf_counter()

    @property
    def duration_seconds(self) -> float:
        end = self.ended_at or time.perf_counter()
        return max(end - self.started_at, 1e-9)

    @property
    def request_count(self) -> int:
        return len(self.requests)

    @property
    def error_count(self) -> int:
        return sum(1 for r in self.requests if r.status_code >= 400)

    @property
    def error_rate(self) -> float:
        if not self.requests:
            return 0.0
        return self.error_count / self.request_count

    @property
    def rps(self) -> float:
        return self.request_count / self.duration_seconds

    @property
    def throughput_bytes_per_sec(self) -> float:
        total = sum(r.bytes_sent + r.bytes_received for r in self.requests)
        return total / self.duration_seconds

    @property
    def latency_ms(self) -> list[float]:
        return [r.latency_ms for r in self.requests]

    @property
    def p50_ms(self) -> float:
        return _percentile(self.latency_ms, 50)

    @property
    def p95_ms(self) -> float:
        return _percentile(self.latency_ms, 95)

    @property
    def p99_ms(self) -> float:
        return _percentile(self.latency_ms, 99)

    @property
    def db_latency_p50_ms(self) -> float:
        return _percentile(self.db_latency_ms, 50)

    @property
    def db_latency_p95_ms(self) -> float:
        return _percentile(self.db_latency_ms, 95)

    @property
    def db_latency_p99_ms(self) -> float:
        return _percentile(self.db_latency_ms, 99)

    @property
    def db_queries_per_request(self) -> float:
        if not self.requests:
            return 0.0
        return self.db_query_count / self.request_count

    @property
    def redis_hit_rate(self) -> Optional[float]:
        total = self.redis_hits + self.redis_misses
        if total == 0:
            return None
        return self.redis_hits / total

    @property
    def network_latency_p50_ms(self) -> float:
        source = self.network_latency_ms or self.latency_ms
        return _percentile(source, 50)

    @property
    def network_latency_p95_ms(self) -> float:
        source = self.network_latency_ms or self.latency_ms
        return _percentile(source, 95)

    @property
    def network_latency_p99_ms(self) -> float:
        source = self.network_latency_ms or self.latency_ms
        return _percentile(source, 99)

    @property
    def cpu_percent_avg(self) -> Optional[float]:
        if not self.cpu_percent_samples:
            return None
        return statistics.fmean(self.cpu_percent_samples)

    @property
    def memory_mb_peak(self) -> Optional[float]:
        if not self.memory_mb_samples:
            return None
        return max(self.memory_mb_samples)

    def record_request(
        self,
        *,
        latency_ms: float,
        status_code: int,
        endpoint: str = "",
        bytes_sent: int = 0,
        bytes_received: int = 0,
    ) -> None:
        self.requests.append(
            RequestSample(
                latency_ms=latency_ms,
                status_code=status_code,
                endpoint=endpoint,
                bytes_sent=bytes_sent,
                bytes_received=bytes_received,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "duration_seconds": round(self.duration_seconds, 3),
            "request_count": self.request_count,
            "rps": round(self.rps, 2),
            "throughput_bytes_per_sec": round(self.throughput_bytes_per_sec, 0),
            "error_count": self.error_count,
            "error_rate": round(self.error_rate, 4),
            "p50_ms": round(self.p50_ms, 2),
            "p95_ms": round(self.p95_ms, 2),
            "p99_ms": round(self.p99_ms, 2),
            "cpu_percent_avg": round(self.cpu_percent_avg, 2) if self.cpu_percent_avg is not None else None,
            "memory_mb_peak": round(self.memory_mb_peak, 2) if self.memory_mb_peak is not None else None,
            "db_query_count": self.db_query_count,
            "db_queries_per_request": round(self.db_queries_per_request, 2),
            "db_latency_p50_ms": round(self.db_latency_p50_ms, 2),
            "db_latency_p95_ms": round(self.db_latency_p95_ms, 2),
            "db_latency_p99_ms": round(self.db_latency_p99_ms, 2),
            "redis_ops": self.redis_ops,
            "redis_hit_rate": round(self.redis_hit_rate, 4) if self.redis_hit_rate is not None else None,
            "network_latency_p50_ms": round(self.network_latency_p50_ms, 2),
            "network_latency_p95_ms": round(self.network_latency_p95_ms, 2),
            "network_latency_p99_ms": round(self.network_latency_p99_ms, 2),
        }

    def format_report(self) -> str:
        d = self.to_dict()
        lines = [
            f"=== Stress metrics: {d['name']} ===",
            f"  RPS:              {d['rps']}",
            f"  Throughput:       {d['throughput_bytes_per_sec']} B/s",
            f"  Requests:         {d['request_count']} in {d['duration_seconds']}s",
            f"  Error rate:       {d['error_rate'] * 100:.2f}% ({d['error_count']} errors)",
            f"  P50 / P95 / P99:  {d['p50_ms']} / {d['p95_ms']} / {d['p99_ms']} ms",
            f"  CPU avg:          {d['cpu_percent_avg'] if d['cpu_percent_avg'] is not None else 'n/a'}%",
            f"  Memory peak:      {d['memory_mb_peak'] if d['memory_mb_peak'] is not None else 'n/a'} MB",
            f"  DB queries:       {d['db_query_count']} ({d['db_queries_per_request']}/req)",
            f"  DB latency P50/P95/P99: {d['db_latency_p50_ms']} / {d['db_latency_p95_ms']} / {d['db_latency_p99_ms']} ms",
            f"  Redis hit rate:   {d['redis_hit_rate'] if d['redis_hit_rate'] is not None else 'n/a'}",
            f"  Network P50/P95/P99: {d['network_latency_p50_ms']} / {d['network_latency_p95_ms']} / {d['network_latency_p99_ms']} ms",
        ]
        return "\n".join(lines)

    def write_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")


@dataclass
class StressSessionReport:
    """All stress runs in one pytest session."""

    runs: list[StressRunMetrics] = field(default_factory=list)

    def add(self, run: StressRunMetrics) -> None:
        self.runs.append(run)

    def format_summary(self) -> str:
        if not self.runs:
            return "No stress metrics collected."
        blocks = [run.format_report() for run in self.runs]
        return "\n\n".join(blocks)

    def write_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"runs": [run.to_dict() for run in self.runs]}
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
