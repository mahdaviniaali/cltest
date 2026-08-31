"""UC-N1..N3 — سناریوهای inbox و اعلان."""

from __future__ import annotations

import pytest

from app.models.match import Match
from helpers.scenario_assertions import assert_inbox_has, assert_status, assert_unread_count
from helpers.scenario_steps import (
    given_user_has_filter,
    system_discovers_new_ad,
    system_runs_full_notify_pipeline,
    system_runs_match_pipeline,
    system_runs_notify_pipeline,
    user_marks_all_read,
    user_marks_read,
    user_opens_inbox,
    user_unread_count,
)

pytestmark = pytest.mark.product


def test_scenario_d1_match_creates_in_app_notification_with_link(ali_client, scenario_db, ali):
    """
    UC-N1 · Given match رخ داده
    When pipeline notify اجرا می‌شود
    Then in-app با title و link
    """
    search = given_user_has_filter(scenario_db, ali, brand="Toyota", model="Camry", name="کمری من")
    ad = system_discovers_new_ad(
        scenario_db,
        bama_id="d1-notify",
        brand="Toyota",
        model="Camry",
        year=1402,
        price=2_900_000_000,
        title="Toyota Camry 1402",
    )
    matches = system_runs_match_pipeline(scenario_db, ad.id)
    system_runs_notify_pipeline(scenario_db, matches[0].id)

    items = assert_inbox_has(ali_client, count=1, title_contains="Toyota")
    assert items[0]["body"]
    assert items[0]["payload"]["ad_url"].startswith("https://")


def test_scenario_d2_duplicate_orchestrate_no_second_delivery(scenario_db, ali):
    """
    UC-N2 · Given notification ارسال شده
    When orchestrate دوباره صدا زده شود
    Then یک delivery per channel
    """
    search = given_user_has_filter(scenario_db, ali, brand="Honda")
    ad = system_discovers_new_ad(
        scenario_db,
        bama_id="d2-dup",
        brand="Honda",
        price=1_800_000_000,
    )
    matches = system_runs_match_pipeline(scenario_db, ad.id)
    system_runs_notify_pipeline(scenario_db, matches[0].id)
    system_runs_notify_pipeline(scenario_db, matches[0].id)

    from app.repositories.notification_repository import NotificationRepository

    rows = NotificationRepository(scenario_db).list_for_user(ali.id)
    in_app = [r for r in rows if r.channel == "in_app"]
    assert len(in_app) == 1


def test_scenario_d3_ali_opens_inbox_list(ali_client, scenario_db, ali):
    """
    UC-N1 · Given یک match notify شده
    When inbox باز می‌شود
    Then لیست notifications
    """
    given_user_has_filter(scenario_db, ali, brand="Mazda")
    ad = system_discovers_new_ad(scenario_db, bama_id="d3-inbox", brand="Mazda", price=2_000_000_000)
    system_runs_full_notify_pipeline(scenario_db, ad.id)

    response = user_opens_inbox(ali_client)
    body = assert_status(response, 200)
    assert len(body) >= 1


def test_scenario_d4_unread_badge_shows_one(ali_client, scenario_db, ali):
    """
    UC-N1 · Given یک اعلان unread
    When unread-count
    Then count=1
    """
    given_user_has_filter(scenario_db, ali, brand="Nissan")
    ad = system_discovers_new_ad(scenario_db, bama_id="d4-badge", brand="Nissan", price=1_500_000_000)
    system_runs_full_notify_pipeline(scenario_db, ad.id)
    assert_unread_count(ali_client, 1)


def test_scenario_d5_ali_marks_one_read(ali_client, scenario_db, ali):
    """
    UC-N1 · Given یک اعلان unread
    When mark read
    Then read_at set و count=0
    """
    given_user_has_filter(scenario_db, ali, brand="Hyundai")
    ad = system_discovers_new_ad(scenario_db, bama_id="d5-read", brand="Hyundai", price=1_200_000_000)
    system_runs_full_notify_pipeline(scenario_db, ad.id)

    notif_id = user_opens_inbox(ali_client).json()[0]["id"]
    read_resp = user_marks_read(ali_client, notif_id)
    body = assert_status(read_resp, 200)
    assert body["read_at"] is not None
    assert_unread_count(ali_client, 0)


def test_scenario_d6_ali_marks_all_read(ali_client, scenario_db, ali):
    """
    UC-N1 · Given چند اعلان unread
    When mark all read
    Then همه read
    """
    given_user_has_filter(scenario_db, ali, brand="Suzuki", model="Vitara")
    given_user_has_filter(scenario_db, ali, brand="Kia", model="Sportage")
    ad1 = system_discovers_new_ad(
        scenario_db, bama_id="d6-a", brand="Suzuki", model="Vitara", price=1_000_000_000
    )
    ad2 = system_discovers_new_ad(
        scenario_db, bama_id="d6-b", brand="Kia", model="Sportage", price=1_100_000_000
    )
    system_runs_full_notify_pipeline(scenario_db, ad1.id)
    system_runs_full_notify_pipeline(scenario_db, ad2.id)

    assert_unread_count(ali_client, 2)
    all_read = user_marks_all_read(ali_client)
    assert_status(all_read, 200)
    assert_unread_count(ali_client, 0)
