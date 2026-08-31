"""UC-U1 — سفر احراز هویت و جداسازی کاربران."""

from __future__ import annotations

import pytest

from helpers.scenario_assertions import assert_not_found, assert_status
from helpers.scenario_steps import (
    given_user_has_filter,
    login_user,
    register_user,
    user_updates_filter,
)

pytestmark = pytest.mark.product


def test_scenario_a1_ali_registers_and_logs_in(bare_client):
    """
    UC-U1 · Given علی کاربر جدید است
    When ثبت‌نام و login می‌کند
    Then /api/auth/me هویت او را برمی‌گرداند
    """
    reg = register_user(bare_client, email="newali@example.com")
    body = assert_status(reg, 201, "ثبت‌نام باید موفق باشد")
    assert body["access_token"]
    assert body["user"]["email"] == "newali@example.com"

    login = login_user(bare_client, email="newali@example.com")
    token_body = assert_status(login, 200, "login باید موفق باشد")
    token = token_body["access_token"]

    me = bare_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    me_body = assert_status(me, 200, "me باید کاربر را برگرداند")
    assert me_body["email"] == "newali@example.com"


def test_scenario_a8_sara_cannot_access_ali_filter(ali_client, sara_client, scenario_db, ali):
    """
    UC-U1 · Given علی یک فیلتر دارد
    When سارا سعی می‌کند فیلتر علی را ببیند یا ویرایش کند
    Then 404 — فیلترهای کاربران جدا هستند
    """
    search = given_user_has_filter(scenario_db, ali, brand="Toyota", model="Camry")

    get_resp = sara_client.get(f"/api/searches/{search.id}")
    assert_not_found(get_resp, "سارا نباید فیلتر علی را ببیند")

    put_resp = user_updates_filter(sara_client, search.id, max_price=2_000_000_000)
    assert_not_found(put_resp, "سارا نباید فیلتر علی را ویرایش کند")
