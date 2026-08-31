"""
Locust load tests against the local API — never hits bama.ir.

Prerequisites:
  1. API running: uvicorn app.api.main:app --host 127.0.0.1 --port 8000
  2. Optional: docker-compose up api postgres redis

Run (read-heavy, no crawl dispatch):
  locust -f tests/load/locustfile.py --headless -u 200 -r 40 -t 3m \\
    --host http://127.0.0.1:8000

Metrics (auto on test_stop):
  RPS, P50/P95/P99, error rate, CPU, memory, throughput, network latency
  JSON report: tests/load/reports/locust_metrics.json

Env:
  STRESS_ALLOW_CRAWL=0  (default) — skip POST endpoints that enqueue crawl jobs
  STRESS_ALLOW_CRAWL=1  — include search create (may enqueue jobs on server)
  STRESS_ASSERT_SLO=1   — fail if Locust run violates SLO thresholds
  STRESS_REPORT_JSON=1  — write JSON metrics report (default on)
"""

from __future__ import annotations

import os
import random
import uuid

from locust import HttpUser, between, task

import tests.load.metrics_reporter  # noqa: F401 — registers event listeners

ALLOW_CRAWL = os.getenv("STRESS_ALLOW_CRAWL", "0") == "1"


class ApiUser(HttpUser):
    wait_time = between(0.01, 0.1)
    token: str | None = None

    def on_start(self) -> None:
        email = f"locust-{uuid.uuid4().hex[:12]}@stress.local"
        password = "stress-pass-123"
        with self.client.post(
            "/api/auth/register",
            json={"email": email, "password": password, "full_name": "Locust"},
            catch_response=True,
        ) as response:
            if response.status_code == 201:
                self.token = response.json()["access_token"]
            elif response.status_code == 409:
                login = self.client.post(
                    "/api/auth/login",
                    json={"email": email, "password": password},
                )
                if login.status_code == 200:
                    self.token = login.json()["access_token"]

    @property
    def auth_headers(self) -> dict[str, str]:
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}

    @task(5)
    def health_live(self) -> None:
        self.client.get("/api/health/live", name="/api/health/live")

    @task(3)
    def metrics(self) -> None:
        self.client.get("/api/metrics", name="/api/metrics")

    @task(10)
    def list_ads(self) -> None:
        self.client.get(
            "/api/ads",
            params={"limit": 50, "offset": random.randint(0, 100)},
            headers=self.auth_headers,
            name="/api/ads",
        )

    @task(8)
    def preview_ads(self) -> None:
        brands = ["Toyota", "Honda", "BMW", "Renault", "Dena"]
        self.client.post(
            "/api/ads/preview",
            json={"brand": random.choice(brands), "limit": 20},
            headers=self.auth_headers,
            name="/api/ads/preview",
        )

    @task(6)
    def list_searches(self) -> None:
        self.client.get("/api/searches", headers=self.auth_headers, name="/api/searches")

    @task(4)
    def notifications(self) -> None:
        self.client.get(
            "/api/notifications",
            headers=self.auth_headers,
            name="/api/notifications",
        )

    @task(4)
    def unread_count(self) -> None:
        self.client.get(
            "/api/notifications/unread-count",
            headers=self.auth_headers,
            name="/api/notifications/unread-count",
        )

    @task(3)
    def taxonomy(self) -> None:
        paths = [
            "/api/taxonomy/sections",
            "/api/taxonomy/brands?section=car",
            "/api/taxonomy/cities?section=car",
        ]
        path = random.choice(paths)
        self.client.get(path, headers=self.auth_headers, name=path.split("?")[0])

    @task(2)
    def inspector_reads(self) -> None:
        paths = [
            "/api/inspector/jobs",
            "/api/inspector/site/tree",
            "/api/inspector/site/map",
            "/api/inspector/stats/overview",
        ]
        path = random.choice(paths)
        self.client.get(path, headers=self.auth_headers, name=path)

    @task(2)
    def auth_me(self) -> None:
        self.client.get("/api/auth/me", headers=self.auth_headers, name="/api/auth/me")

    @task(1)
    def data_status(self) -> None:
        self.client.get("/api/data/status", headers=self.auth_headers, name="/api/data/status")

    @task(1)
    def health_ready(self) -> None:
        """Probes DB + Redis — contributes to redis hit tracking on server."""
        self.client.get("/api/health/ready", name="/api/health/ready")

    @task(0 if not ALLOW_CRAWL else 1)
    def create_search(self) -> None:
        if not ALLOW_CRAWL:
            return
        self.client.post(
            "/api/searches",
            json={
                "brand": random.choice(["Toyota", "Honda"]),
                "enabled": True,
            },
            headers=self.auth_headers,
            name="/api/searches [create]",
        )
