"""ADR-011 — سناریوهای چندکاربره و fingerprint مشترک."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from app.models.filter_crawl_state import FilterCrawlState
from app.repositories.filter_crawl_state_repository import FilterCrawlStateRepository
from helpers.scenario_assertions import assert_status, assert_unread_count
from helpers.scenario_factory import AdFactory, FilterFactory, UserFactory
from helpers.scenario_steps import (
    given_user_has_filter,
    system_discovers_new_ad,
    system_runs_full_notify_pipeline,
    user_creates_filter,
)

pytestmark = pytest.mark.product


@patch("app.api.routes.searches.dispatch_on_demand_job")
def test_scenario_b8_ali_and_sara_share_one_crawl_job(mock_dispatch, ali_client, sara_client, scenario_db, ali, sara):
    """
    B8 · Given علی و سارا همان فیلتر Porsche Panamera می‌خواهند
    When علی create می‌کند و سارا بعداً همان را create می‌کند
    Then یک job مشترک — duplicate enqueue نشود
    """
    first = user_creates_filter(ali_client, brand="Porsche", model="Panamera")
    first_body = assert_status(first, 201)
    first_job = first_body["job_id"]
    mock_dispatch.reset_mock()

    second = user_creates_filter(sara_client, brand="Porsche", model="Panamera")
    second_body = assert_status(second, 201)

    assert second_body["filter_fingerprint"] == first_body["filter_fingerprint"]
    if second_body.get("job_id") and first_job:
        assert second_body["job_id"] == first_job, "سارا باید همان job مشترک را ببیند"


def test_scenario_e1_beat_prioritizes_popular_benz_filter(scenario_db):
    """
    E1 · Given 5 کاربر بنز E200 و 1 کاربر تویوتا — هر دو stale
    When beat stale filters را لیست می‌کند
    Then بنز (user-count بالاتر) اول schedule می‌شود
    """
    benz_fp = None
    for i in range(5):
        user = UserFactory.create(scenario_db, email=f"benz{i}@test.com")
        search = FilterFactory.create_search(
            scenario_db, user.id, brand="Benz", model="E200"
        )
        benz_fp = search.filter_fingerprint

    toyota_user = UserFactory.create(scenario_db, email="toyota@test.com")
    toyota_search = FilterFactory.create_search(
        scenario_db, toyota_user.id, brand="Toyota", model="Camry"
    )

    old = datetime.now(timezone.utc) - timedelta(hours=2)
    for fp in {benz_fp, toyota_search.filter_fingerprint}:
        state = scenario_db.get(FilterCrawlState, fp)
        state.last_crawl_at = old
    scenario_db.commit()

    stale = FilterCrawlStateRepository(scenario_db).list_stale_active(
        max_age_seconds=300,
        limit=10,
    )
    assert len(stale) >= 2
    assert stale[0].fingerprint == benz_fp
    assert stale[0].enabled_search_count == 5


def test_scenario_e2_same_filter_both_users_get_notified(ali_client, sara_client, scenario_db, ali, sara):
    """
    E2 · Given علی و سارا فیلتر یکسان دارند
    When آگهی matching کشف می‌شود
    Then هر دو notify می‌شوند
    """
    given_user_has_filter(scenario_db, ali, brand="Toyota", model="Yaris")
    given_user_has_filter(scenario_db, sara, brand="Toyota", model="Yaris")

    ad = system_discovers_new_ad(
        scenario_db,
        bama_id="e2-shared",
        brand="Toyota",
        model="Yaris",
        year=1401,
        price=1_800_000_000,
    )
    system_runs_full_notify_pipeline(scenario_db, ad.id)

    assert_unread_count(ali_client, 1)
    assert_unread_count(sara_client, 1)


@patch("app.api.routes.searches.dispatch_on_demand_job")
def test_scenario_e3_filter_change_rematches_cached_ads(
    mock_dispatch, ali_client, scenario_db, ali
):
    """
    E3 · Given cache کافی برای فیلتر جدید
    When علی brand را عوض می‌کند
    Then rematch با criteria جدید (بدون crawl)
    """
    AdFactory.seed_matching_ads(
        scenario_db, brand="Toyota", model="Camry", count=5, prefix="e3"
    )
    warm = FilterFactory.create_search(scenario_db, ali.id, brand="Toyota", model="Camry")
    FilterFactory.mark_fresh(scenario_db, warm)

    search = given_user_has_filter(scenario_db, ali, brand="Dena", model="Plus")
    FilterFactory.mark_fresh(scenario_db, search)

    from helpers.scenario_steps import user_updates_filter

    response = user_updates_filter(ali_client, search.id, brand="Toyota", model="Camry")
    body = assert_status(response, 200)
    assert body.get("cache_sufficient") is True
    mock_dispatch.assert_not_called()

    from sqlalchemy import select
    from app.models.match import Match

    matches = list(
        scenario_db.scalars(select(Match).where(Match.search_id == search.id))
    )
    assert len(matches) >= 1
