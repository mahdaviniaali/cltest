from __future__ import annotations

from typing import Any, Optional

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.advertisement import Advertisement
from app.models.search import Search
from app.models.user import User
from app.services.matching import MatchingService
from app.services.notification_orchestrator import NotificationOrchestrator
from .scenario_factory import AdFactory, FilterFactory


def register_user(client: TestClient, *, email: str, password: str = "secret123") -> dict:
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": "کاربر تست"},
    )
    return response


def login_user(client: TestClient, *, email: str, password: str = "secret123") -> dict:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    return response


def user_creates_filter(
    client: TestClient,
    *,
    brand: Optional[str] = None,
    model: Optional[str] = None,
    min_year: Optional[int] = None,
    max_price: Optional[int] = None,
    max_mileage: Optional[int] = None,
    location: Optional[str] = None,
    enabled: bool = True,
    name: Optional[str] = None,
) -> dict:
    payload: dict[str, Any] = {"enabled": enabled}
    if brand is not None:
        payload["brand"] = brand
    if model is not None:
        payload["model"] = model
    if min_year is not None:
        payload["min_year"] = min_year
    if max_price is not None:
        payload["max_price"] = max_price
    if max_mileage is not None:
        payload["max_mileage"] = max_mileage
    if location is not None:
        payload["location"] = location
    if name is not None:
        payload["name"] = name
    response = client.post("/api/searches", json=payload)
    return response


def user_lists_filters(client: TestClient) -> dict:
    return client.get("/api/searches")


def user_updates_filter(client: TestClient, search_id: int, **fields: Any) -> dict:
    return client.put(f"/api/searches/{search_id}", json=fields)


def user_deletes_filter(client: TestClient, search_id: int) -> dict:
    return client.delete(f"/api/searches/{search_id}")


def user_toggles_filter(client: TestClient, search_id: int) -> dict:
    return client.patch(f"/api/searches/{search_id}/toggle")


def user_previews_ads(client: TestClient, **criteria: Any) -> dict:
    return client.post("/api/ads/preview", json=criteria)


def user_opens_filter_results(client: TestClient, search_id: int) -> dict:
    return client.get(f"/api/searches/{search_id}/results")


def user_refreshes_filter(client: TestClient, search_id: int, *, force: bool = False) -> dict:
    url = f"/api/searches/{search_id}/refresh"
    if force:
        url += "?force=true"
    return client.post(url)


def user_refreshes_global_data(client: TestClient) -> dict:
    return client.post("/api/crawl/refresh")


def user_opens_inbox(client: TestClient) -> dict:
    return client.get("/api/notifications")


def user_unread_count(client: TestClient) -> dict:
    return client.get("/api/notifications/unread-count")


def user_marks_read(client: TestClient, notification_id: int) -> dict:
    return client.patch(f"/api/notifications/{notification_id}/read")


def user_marks_all_read(client: TestClient) -> dict:
    return client.post("/api/notifications/read-all")


def system_discovers_new_ad(session: Session, **kwargs: Any) -> Advertisement:
    ad, _ = AdFactory.discover_new(session, **kwargs)
    return ad


def system_runs_match_pipeline(session: Session, ad_id: int) -> list:
    matches = MatchingService(session).process_new_ad(ad_id)
    session.commit()
    return matches


def system_runs_notify_pipeline(session: Session, match_id: int) -> dict:
    result = NotificationOrchestrator(session).orchestrate(match_id)
    session.commit()
    return result


def system_runs_full_notify_pipeline(session: Session, ad_id: int) -> list:
    matches = system_runs_match_pipeline(session, ad_id)
    for match in matches:
        system_runs_notify_pipeline(session, match.id)
    return matches


def given_user_has_filter(
    session: Session,
    user: User,
    *,
    brand: Optional[str] = None,
    model: Optional[str] = None,
    min_year: Optional[int] = None,
    max_price: Optional[int] = None,
    max_mileage: Optional[int] = None,
    location: Optional[str] = None,
    enabled: bool = True,
    name: Optional[str] = None,
) -> Search:
    return FilterFactory.create_search(
        session,
        user.id,
        brand=brand,
        model=model,
        min_year=min_year,
        max_price=max_price,
        max_mileage=max_mileage,
        location=location,
        enabled=enabled,
        name=name,
    )
