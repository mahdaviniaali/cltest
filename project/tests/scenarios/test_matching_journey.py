"""UC-M1..M3 — سناریوهای matching آگهی جدید با فیلتر."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models.match import Match
from app.models.outbox_event import OutboxEvent
from helpers.scenario_steps import (
    given_user_has_filter,
    system_discovers_new_ad,
    system_runs_match_pipeline,
)

pytestmark = pytest.mark.product


def test_scenario_c1_new_toyota_camry_matches_ali_filter(scenario_db, ali):
    """
    UC-M1/M3 · Given علی فیلتر تویوتا کمری 1400+ دارد
    When آگهی جدید تویوتا کمری 1402 کشف می‌شود
    Then 1 match و outbox notify.requested
    """
    search = given_user_has_filter(
        scenario_db, ali, brand="Toyota", model="Camry", min_year=1400
    )
    ad = system_discovers_new_ad(
        scenario_db,
        bama_id="c1-toyota",
        brand="Toyota",
        model="Camry",
        year=1402,
        price=2_800_000_000,
        location="Tehran",
    )
    matches = system_runs_match_pipeline(scenario_db, ad.id)
    assert len(matches) == 1
    assert matches[0].search_id == search.id

    notify_events = list(
        scenario_db.scalars(
            select(OutboxEvent).where(OutboxEvent.event_type == "notify.requested")
        )
    )
    assert len(notify_events) == 1


def test_scenario_c2_bmw_ad_does_not_match_toyota_filter(scenario_db, ali):
    """
    UC-M2 · Given فیلتر تویوتا
    When آگهی BMW می‌آید
    Then 0 match
    """
    given_user_has_filter(scenario_db, ali, brand="Toyota", model="Camry")
    ad = system_discovers_new_ad(
        scenario_db,
        bama_id="c2-bmw",
        brand="BMW",
        model="320",
        year=1402,
        price=4_000_000_000,
    )
    matches = system_runs_match_pipeline(scenario_db, ad.id)
    assert len(matches) == 0


def test_scenario_c3_year_below_min_no_match(scenario_db, ali):
    """
    UC-M2 · Given min_year=1400
    When آگهی سال 1390
    Then 0 match
    """
    given_user_has_filter(scenario_db, ali, brand="Toyota", min_year=1400)
    ad = system_discovers_new_ad(
        scenario_db,
        bama_id="c3-old-year",
        brand="Toyota",
        model="Corolla",
        year=1390,
        price=1_000_000_000,
    )
    assert len(system_runs_match_pipeline(scenario_db, ad.id)) == 0


def test_scenario_c4_price_above_max_no_match(scenario_db, ali):
    """
    UC-M2 · Given max_price=3B
    When آگهی 4B
    Then 0 match
    """
    given_user_has_filter(scenario_db, ali, brand="Toyota", max_price=3_000_000_000)
    ad = system_discovers_new_ad(
        scenario_db,
        bama_id="c4-expensive",
        brand="Toyota",
        year=1402,
        price=4_000_000_000,
    )
    assert len(system_runs_match_pipeline(scenario_db, ad.id)) == 0


def test_scenario_c5_mileage_above_max_no_match(scenario_db, ali):
    """
    UC-M2 · Given max_mileage=100k
    When آگهی 150k km
    Then 0 match
    """
    given_user_has_filter(scenario_db, ali, brand="Toyota", max_mileage=100_000)
    ad = system_discovers_new_ad(
        scenario_db,
        bama_id="c5-high-km",
        brand="Toyota",
        mileage=150_000,
        price=1_500_000_000,
    )
    assert len(system_runs_match_pipeline(scenario_db, ad.id)) == 0


def test_scenario_c6_wrong_location_no_match(scenario_db, ali):
    """
    UC-M2 · Given location=اصفهان
    When آگهی تهران
    Then 0 match
    """
    given_user_has_filter(scenario_db, ali, brand="Toyota", location="اصفهان")
    ad = system_discovers_new_ad(
        scenario_db,
        bama_id="c6-tehran",
        brand="Toyota",
        location="تهران",
        price=2_000_000_000,
    )
    assert len(system_runs_match_pipeline(scenario_db, ad.id)) == 0


def test_scenario_c7_disabled_filter_no_match(scenario_db, ali):
    """
    UC-M1 · Given فیلتر disabled
    When آگهی matching می‌آید
    Then 0 match
    """
    given_user_has_filter(scenario_db, ali, brand="Toyota", enabled=False)
    ad = system_discovers_new_ad(
        scenario_db,
        bama_id="c7-disabled",
        brand="Toyota",
        price=2_000_000_000,
    )
    assert len(system_runs_match_pipeline(scenario_db, ad.id)) == 0


def test_scenario_c8_same_ad_processed_twice_idempotent(scenario_db, ali):
    """
    UC-M3/N2 · Given match قبلاً ثبت شده
    When همان ad دوباره process شود
    Then match جدید ساخته نمی‌شود
    """
    search = given_user_has_filter(scenario_db, ali, brand="Toyota")
    ad = system_discovers_new_ad(
        scenario_db,
        bama_id="c8-dup",
        brand="Toyota",
        price=2_000_000_000,
    )
    first = system_runs_match_pipeline(scenario_db, ad.id)
    assert len(first) == 1
    second = system_runs_match_pipeline(scenario_db, ad.id)
    assert len(second) == 0

    match_row = scenario_db.scalar(
        select(Match).where(Match.ad_id == ad.id, Match.search_id == search.id)
    )
    assert match_row is not None


def test_scenario_c9_model_only_filter_matches_any_brand_camry(scenario_db, ali):
    """
    UC-M2 · Given فیلتر فقط model=Camry (بدون برند)
    When آگهی Toyota Camry
    Then match — کاربر فقط مدل را می‌خواهد
    """
    search = given_user_has_filter(scenario_db, ali, model="Camry", min_year=1400)
    ad = system_discovers_new_ad(
        scenario_db,
        bama_id="c9-model-only",
        brand="Toyota",
        model="Camry",
        year=1401,
        price=2_500_000_000,
    )
    matches = system_runs_match_pipeline(scenario_db, ad.id)
    assert len(matches) == 1
    assert matches[0].search_id == search.id
