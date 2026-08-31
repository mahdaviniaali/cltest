"""ADR-006/011 — سناریوهای cache-first و داده."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from app.models.crawl_job import CrawlJob, CrawlJobStatus, CrawlJobType
from helpers.scenario_assertions import assert_cache_hit, assert_crawl_enqueued, assert_status
from helpers.scenario_factory import AdFactory, FilterFactory
from helpers.scenario_steps import (
    given_user_has_filter,
    user_creates_filter,
    user_opens_filter_results,
    user_previews_ads,
    user_refreshes_filter,
    user_refreshes_global_data,
    user_updates_filter,
)

pytestmark = pytest.mark.product


@patch("app.api.routes.searches.dispatch_on_demand_job")
def test_scenario_b1_ali_creates_filter_empty_cache_starts_crawl(mock_dispatch, ali_client):
    """
    B1 · Given cache خالی است
    When علی فیلتر جدید می‌سازد
    Then is_crawling=true و پیام بروزرسانی
    """
    response = user_creates_filter(ali_client, brand="Dena", model="Plus")
    body = assert_status(response, 201)
    assert_crawl_enqueued(body)
    assert "بروزرسانی" in body.get("message", "") or body["is_crawling"]
    mock_dispatch.assert_called_once()


@patch("app.api.routes.searches.dispatch_on_demand_job")
def test_scenario_b2_ali_creates_filter_with_warm_cache_instant_results(mock_dispatch, ali_client, scenario_db):
    """
    B2 · Given 5+ آگهی matching تازه در DB
    When علی همان فیلتر را می‌سازد
    Then cache_sufficient=true و crawl نمی‌رود
    """
    AdFactory.seed_matching_ads(scenario_db, brand="Dena", model="Plus", count=5, prefix="warm")
    response = user_creates_filter(ali_client, brand="Dena", model="Plus")
    body = assert_status(response, 201)
    assert_cache_hit(body)
    assert body["cached_count"] >= 5
    mock_dispatch.assert_not_called()


def test_scenario_b3_ali_previews_before_save_no_crawl(ali_client, scenario_db):
    """
    B3 · Given آگهی‌های تویوتا در cache
    When علی preview می‌زند (بدون save)
    Then ads برمی‌گردد و crawl enqueue نمی‌شود
    """
    AdFactory.seed_matching_ads(scenario_db, brand="Toyota", count=3, prefix="preview")
    response = user_previews_ads(ali_client, brand="Toyota", limit=10)
    body = assert_status(response, 200)
    assert body["total_count"] >= 1
    assert body["is_refreshing"] is False


def test_scenario_b4_ali_opens_filter_results_page(ali_client, scenario_db, ali):
    """
    B4 · Given علی فیلتر هوندا دارد و آگهی matching وجود دارد
    When /searches/{id}/results باز می‌کند
    Then total_count و last_updated_at نمایش داده می‌شود
    """
    search = given_user_has_filter(scenario_db, ali, brand="Honda", model="Civic")
    AdFactory.seed_matching_ads(scenario_db, brand="Honda", model="Civic", count=2, prefix="results")
    FilterFactory.mark_fresh(scenario_db, search)

    response = user_opens_filter_results(ali_client, search.id)
    body = assert_status(response, 200)
    assert body["total_count"] >= 1
    assert "last_updated_at" in body
    assert "bootstrapped" in body
    assert "cache_sufficient" in body


@patch("app.api.routes.searches.dispatch_on_demand_job")
def test_scenario_b5_ali_manual_refresh_starts_job(mock_dispatch, ali_client, scenario_db, ali):
    """
    B5 · Given فیلتر علی stale است
    When refresh دستی می‌زند
    Then 202 + job_id + is_refreshing
    """
    search = given_user_has_filter(scenario_db, ali, brand="Peugeot", model="206")
    response = user_refreshes_filter(ali_client, search.id)
    body = assert_status(response, 202)
    assert body["is_refreshing"] is True
    assert body["job_id"]
    mock_dispatch.assert_called_once()


@patch("app.api.routes.searches.dispatch_on_demand_job")
def test_scenario_b6_refresh_while_crawl_running_is_idempotent(mock_dispatch, ali_client, scenario_db, ali):
    """
    B6 · Given crawl برای fingerprint در جریان است
    When علی refresh می‌زند
    Then duplicate job enqueue نمی‌شود
    """
    search = given_user_has_filter(scenario_db, ali, brand="Kia", model="Cerato")
    fp = search.filter_fingerprint
    scenario_db.add(
        CrawlJob(
            id="running-kia-1",
            job_type=CrawlJobType.ON_DEMAND_FILTER.value,
            status=CrawlJobStatus.RUNNING.value,
            triggered_by="test",
            filter_fingerprint=fp,
            idempotency_key="test-running-kia",
            started_at=datetime.now(timezone.utc),
        )
    )
    scenario_db.commit()

    response = user_refreshes_filter(ali_client, search.id)
    body = assert_status(response, 202)
    assert body["is_refreshing"] is True, "کاربر باید ببیند crawl در جریان است"
    jobs = [
        j
        for j in scenario_db.query(CrawlJob).all()
        if j.filter_fingerprint == fp
    ]
    assert len(jobs) == 1, "نباید job تکراری برای همان fingerprint ساخته شود"


@patch("app.api.routes.searches.dispatch_on_demand_job")
def test_scenario_b7_ali_changes_brand_new_fingerprint_and_crawl(mock_dispatch, ali_client, scenario_db, ali):
    """
    B7 · Given علی فیلتر Dena دارد
    When برند را به Toyota عوض می‌کند
    Then fingerprint جدید و crawl enqueue
    """
    search = given_user_has_filter(scenario_db, ali, brand="Dena", model="Plus")
    old_fp = search.filter_fingerprint

    response = user_updates_filter(ali_client, search.id, brand="Toyota", model="Camry")
    body = assert_status(response, 200)
    assert body["filter_fingerprint"] != old_fp
    assert_crawl_enqueued(body)
    mock_dispatch.assert_called_once()


@patch("app.api.routes.crawl.dispatch_on_demand_job")
def test_scenario_b9_global_refresh_updates_baseline(mock_dispatch, ali_client):
    """
    B9 · When علی global refresh می‌زند
    Then 202 neutral و crawl global شروع می‌شود
    """
    response = user_refreshes_global_data(ali_client)
    body = assert_status(response, 202)
    assert body["is_refreshing"] is True
    assert "بروزرسانی" in body["message"]
    mock_dispatch.assert_called_once()
