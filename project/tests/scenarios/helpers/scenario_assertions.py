from __future__ import annotations

from typing import Any, Optional

from fastapi.testclient import TestClient


def assert_status(response, expected: int, message: str = "") -> dict:
    assert response.status_code == expected, (
        f"{message} — expected {expected}, got {response.status_code}: {response.text}"
    )
    if response.status_code == 204:
        return {}
    return response.json()


def assert_crawl_enqueued(body: dict, *, message: str = "باید crawl شروع شود") -> None:
    assert body.get("is_crawling") is True, message
    assert body.get("job_id"), message


def assert_cache_hit(body: dict, *, message: str = "باید از cache سرو شود") -> None:
    assert body.get("is_crawling") is False, message
    assert body.get("cache_sufficient") is True, message


def assert_fingerprint_present(body: dict) -> str:
    fp = body.get("filter_fingerprint")
    assert fp, "filter_fingerprint باید در پاسخ باشد"
    return fp


def assert_inbox_has(
    client: TestClient,
    *,
    count: int,
    title_contains: Optional[str] = None,
) -> list[dict]:
    response = client.get("/api/notifications")
    assert response.status_code == 200, response.text
    items = response.json()
    assert len(items) == count, f"علی باید {count} اعلان در inbox داشته باشد، دارد {len(items)}"
    if title_contains:
        assert any(title_contains in (item.get("title") or "") for item in items)
    return items


def assert_unread_count(client: TestClient, expected: int) -> None:
    response = client.get("/api/notifications/unread-count")
    assert response.status_code == 200
    actual = response.json()["count"]
    assert actual == expected, f"unread count باید {expected} باشد، هست {actual}"


def assert_filter_count(client: TestClient, expected: int) -> list[dict]:
    response = client.get("/api/searches")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == expected, f"باید {expected} فیلتر باشد، هست {len(items)}"
    return items


def assert_not_found(response, message: str = "باید 404 برگردد") -> None:
    assert response.status_code == 404, message
