"""UC-U2..U7 — سفر CRUD فیلتر کاربر."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from helpers.scenario_assertions import assert_crawl_enqueued, assert_filter_count, assert_fingerprint_present, assert_status
from helpers.scenario_steps import (
    given_user_has_filter,
    system_discovers_new_ad,
    system_runs_match_pipeline,
    user_creates_filter,
    user_deletes_filter,
    user_lists_filters,
    user_toggles_filter,
    user_updates_filter,
)

pytestmark = pytest.mark.product


@patch("app.api.routes.searches.dispatch_on_demand_job")
def test_scenario_a2_ali_creates_first_toyota_camry_filter(mock_dispatch, ali_client):
    """
    UC-U2 · Given علی لاگین است و cache خالی است
    When اولین فیلتر «تویوتا کمری» می‌سازد
    Then 201 + filter_fingerprint + crawl شروع می‌شود
    """
    response = user_creates_filter(ali_client, brand="Toyota", model="Camry", name="تویوتا کمری")
    body = assert_status(response, 201)
    assert_fingerprint_present(body)
    assert_crawl_enqueued(body)
    mock_dispatch.assert_called_once()


@patch("app.api.routes.searches.dispatch_on_demand_job")
def test_scenario_a3_ali_adds_second_bmw_filter(mock_dispatch, ali_client):
    """
    UC-U7 · Given علی یک فیلتر دارد
    When فیلتر دوم BMW 320 اضافه می‌کند
    Then لیست 2 فیلتر مستقل دارد
    """
    user_creates_filter(ali_client, brand="Toyota", model="Camry")
    user_creates_filter(ali_client, brand="BMW", model="320")
    items = assert_filter_count(ali_client, 2)
    brands = {item["brand"] for item in items}
    assert brands == {"Toyota", "BMW"}


@patch("app.api.routes.searches.dispatch_on_demand_job")
def test_scenario_a4_ali_lists_only_own_filters(mock_dispatch, ali_client, scenario_db, ali, sara):
    """
    UC-U3 · Given علی و سارا هر کدام فیلتر دارند
    When علی لیست می‌گیرد
    Then فقط فیلترهای خودش را می‌بیند
    """
    user_creates_filter(ali_client, brand="Toyota", model="Camry")
    given_user_has_filter(scenario_db, sara, brand="BMW", model="320")

    response = user_lists_filters(ali_client)
    body = assert_status(response, 200)
    assert len(body) == 1
    assert body[0]["brand"] == "Toyota"


@patch("app.api.routes.searches.dispatch_on_demand_job")
def test_scenario_a5_ali_lowers_max_price_triggers_new_crawl(mock_dispatch, ali_client, scenario_db, ali):
    """
    UC-U4 · Given علی فیلتر بنز با max_price=5B دارد
    When max_price را به 3B کم می‌کند
    Then fingerprint عوض می‌شود و crawl جدید enqueue می‌شود
    """
    search = given_user_has_filter(scenario_db, ali, brand="Benz", max_price=5_000_000_000)
    old_fp = search.filter_fingerprint

    response = user_updates_filter(ali_client, search.id, max_price=3_000_000_000)
    body = assert_status(response, 200)
    assert body["filter_fingerprint"] != old_fp
    assert_crawl_enqueued(body)
    mock_dispatch.assert_called_once()


def test_scenario_a6_ali_deletes_bmw_filter(ali_client, scenario_db, ali):
    """
    UC-U5 · Given علی فیلتر BMW دارد
    When آن را حذف می‌کند
    Then 204 و دیگر در لیست نیست
    """
    search = given_user_has_filter(scenario_db, ali, brand="BMW", model="320")
    response = user_deletes_filter(ali_client, search.id)
    assert_status(response, 204)
    assert_filter_count(ali_client, 0)


def test_scenario_a7_disabled_filter_does_not_match(ali_client, scenario_db, ali):
    """
    UC-U6 · Given علی فیلتر تویوتا دارد و آن را خاموش می‌کند
    When آگهی جدید تویوتا کشف می‌شود
    Then match ثبت نمی‌شود
    """
    search = given_user_has_filter(scenario_db, ali, brand="Toyota", model="Camry")
    toggle = user_toggles_filter(ali_client, search.id)
    body = assert_status(toggle, 200)
    assert body["enabled"] is False

    ad = system_discovers_new_ad(
        scenario_db,
        bama_id="toy-disabled-1",
        brand="Toyota",
        model="Camry",
        year=1402,
        price=2_800_000_000,
    )
    matches = system_runs_match_pipeline(scenario_db, ad.id)
    assert len(matches) == 0

    re_toggle = user_toggles_filter(ali_client, search.id)
    assert assert_status(re_toggle, 200)["enabled"] is True


def test_scenario_a7b_reenabled_filter_matches_again(ali_client, scenario_db, ali):
    """
    UC-U6 · Given فیلتر خاموش بود و دوباره روشن شد
    When آگهی جدید می‌آید
    Then match ثبت می‌شود
    """
    search = given_user_has_filter(scenario_db, ali, brand="Honda", model="Civic", enabled=False)
    search.enabled = True
    scenario_db.commit()

    ad = system_discovers_new_ad(
        scenario_db,
        bama_id="honda-on-1",
        brand="Honda",
        model="Civic",
        year=1400,
        price=1_500_000_000,
    )
    matches = system_runs_match_pipeline(scenario_db, ad.id)
    assert len(matches) == 1
    assert matches[0].search_id == search.id
