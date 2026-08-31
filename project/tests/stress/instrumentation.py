"""Instrumentation helpers for stress metrics collection."""

from __future__ import annotations

import threading
import time
from contextlib import contextmanager
from typing import Generator, Optional
from unittest.mock import MagicMock, patch

from sqlalchemy import event
from sqlalchemy.engine import Engine

from tests.stress.metrics import StressRunMetrics

try:
    import psutil

    _HAS_PSUTIL = True
except ImportError:
    _HAS_PSUTIL = False


class DbQueryInstrument:
    """Track SQL query count and latency via SQLAlchemy events."""

    def __init__(self) -> None:
        self.query_count = 0
        self.latency_ms: list[float] = []
        self._starts: dict[int, float] = {}

    def attach(self, engine: Engine) -> None:
        @event.listens_for(engine, "before_cursor_execute")
        def _before(conn, cursor, statement, parameters, context, executemany) -> None:
            self._starts[id(cursor)] = time.perf_counter()

        @event.listens_for(engine, "after_cursor_execute")
        def _after(conn, cursor, statement, parameters, context, executemany) -> None:
            start = self._starts.pop(id(cursor), None)
            if start is None:
                return
            self.query_count += 1
            self.latency_ms.append((time.perf_counter() - start) * 1000.0)

    def sync_to(self, metrics: StressRunMetrics) -> None:
        metrics.db_query_count += self.query_count
        metrics.db_latency_ms.extend(self.latency_ms)

    def reset(self) -> None:
        self.query_count = 0
        self.latency_ms.clear()
        self._starts.clear()


class RedisInstrument:
    """Track Redis operations and hit/miss ratio (ping = hit, exception = miss)."""

    def __init__(self) -> None:
        self.ops = 0
        self.hits = 0
        self.misses = 0

    @contextmanager
    def patch_redis(self, *, use_mock: bool = False) -> Generator[None, None, None]:
        import redis

        original_from_url = redis.from_url
        instrument = self

        def wrapped_from_url(url, **kwargs):
            if use_mock:
                instrument.ops += 1
                instrument.hits += 1
                mock = MagicMock()
                mock.ping.return_value = True
                return mock

            client = original_from_url(url, **kwargs)
            original_ping = client.ping
            original_execute = getattr(client, "execute_command", None)

            def tracked_ping(*args, **kwargs):
                instrument.ops += 1
                try:
                    result = original_ping(*args, **kwargs)
                    instrument.hits += 1
                    return result
                except Exception:
                    instrument.misses += 1
                    raise

            client.ping = tracked_ping  # type: ignore[method-assign]

            if original_execute is not None:

                def tracked_execute(*args, **kwargs):
                    instrument.ops += 1
                    try:
                        result = original_execute(*args, **kwargs)
                        instrument.hits += 1
                        return result
                    except Exception:
                        instrument.misses += 1
                        raise

                client.execute_command = tracked_execute  # type: ignore[method-assign]

            return client

        with patch.object(redis, "from_url", wrapped_from_url):
            yield

    def sync_to(self, metrics: StressRunMetrics) -> None:
        metrics.redis_ops += self.ops
        metrics.redis_hits += self.hits
        metrics.redis_misses += self.misses

    def reset(self) -> None:
        self.ops = 0
        self.hits = 0
        self.misses = 0


class SystemSampler:
    """Background CPU and memory sampling during a burst."""

    def __init__(self, interval_seconds: float = 0.1) -> None:
        self.interval_seconds = interval_seconds
        self.cpu_samples: list[float] = []
        self.memory_mb_samples: list[float] = []
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._process = psutil.Process() if _HAS_PSUTIL else None

    def start(self) -> None:
        if not _HAS_PSUTIL or self._process is None:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._sample_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._thread is None:
            return
        self._stop.set()
        self._thread.join(timeout=2.0)
        self._thread = None

    def _sample_loop(self) -> None:
        assert self._process is not None
        self._process.cpu_percent(interval=None)
        while not self._stop.is_set():
            self.cpu_samples.append(self._process.cpu_percent(interval=None))
            mem = self._process.memory_info().rss / (1024 * 1024)
            self.memory_mb_samples.append(mem)
            self._stop.wait(self.interval_seconds)

    def sync_to(self, metrics: StressRunMetrics) -> None:
        metrics.cpu_percent_samples.extend(self.cpu_samples)
        metrics.memory_mb_samples.extend(self.memory_mb_samples)

    @contextmanager
    def sample(self) -> Generator[None, None, None]:
        self.cpu_samples.clear()
        self.memory_mb_samples.clear()
        self.start()
        try:
            yield
        finally:
            self.stop()
