"""سناریوهای End-to-End — مسیر کامل محصول."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from helpers.scenario_assertions import assert_inbox_has, assert_status, assert_unread_count
from helpers.scenario_steps import (
    system_discovers_new_ad,
    system_runs_full_notify_pipeline,
    user_creates_filter,
    user_opens_inbox,
)

pytestmark = pytest.mark.product


@patch("app.api.routes.searches.dispatch_on_demand_job")
def test_scenario_f1_official_e2e_ali_toyota_filter_to_notification(mock_dispatch, ali_client, scenario_db, ali):
    """
    F1 · سناریوی رسمی تعریف_پروژه:
    علی فیلتر تویوتا کمری می‌سازد → آگهی جدید کشف → match → notify
    """
    # 1. علی فیلتر می‌سازد
    create = user_creates_filter(
        ali_client,
        brand="Toyota",
        model="Camry",
        min_year=1400,
        max_price=3_000_000_000,
        name="تویوتا کمری من",
    )
    create_body = assert_status(create, 201)
    search_id = create_body["id"]

    # 2. سیستم آگهی جدید تویوتا کمری 1402 را کشف می‌کند
    ad = system_discovers_new_ad(
        scenario_db,
        bama_id="f1-e2e-toyota",
        brand="Toyota",
        model="Camry",
        year=1402,
        price=2_900_000_000,
        location="Tehran",
        title="Toyota Camry 1402",
    )

    # 3-4. matching + notification
    matches = system_runs_full_notify_pipeline(scenario_db, ad.id)
    assert len(matches) == 1
    assert matches[0].search_id == search_id

    # 5. علی اعلان در inbox دارد
    items = assert_inbox_has(ali_client, count=1, title_contains="Toyota")
    assert "2" in (items[0]["body"] or "") or "Camry" in (items[0]["title"] or "")
    assert_unread_count(ali_client, 1)


@patch("app.api.routes.searches.dispatch_on_demand_job")
def test_scenario_f2_beat_stale_filter_then_new_ad_reaches_inbox(
    _mock_dispatch, ali_client, scenario_db, ali
):
    """
    F2 · Given فیلتر stale است
    When beat job enqueue می‌کند و بعداً آگهی جدید simulate می‌شود
    Then مسیر match → inbox کامل است
    """
    from datetime import datetime, timedelta, timezone

    from app.models.filter_crawl_state import FilterCrawlState
    from app.services.filter_crawl_service import FilterCrawlService
    from helpers.scenario_steps import given_user_has_filter

    search = given_user_has_filter(
        scenario_db, ali, brand="Toyota", model="Corolla", min_year=1399
    )
    state = scenario_db.get(FilterCrawlState, search.filter_fingerprint)
    state.last_crawl_at = datetime.now(timezone.utc) - timedelta(hours=2)
    scenario_db.commit()

    job_ids = FilterCrawlService(scenario_db).enqueue_stale_active_filters()
    assert len(job_ids) >= 1

    ad = system_discovers_new_ad(
        scenario_db,
        bama_id="f2-beat-ad",
        brand="Toyota",
        model="Corolla",
        year=1401,
        price=2_500_000_000,
    )
    system_runs_full_notify_pipeline(scenario_db, ad.id)

    inbox = user_opens_inbox(ali_client)
    assert len(inbox.json()) >= 1
