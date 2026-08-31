"""Matching and outbox fanout under high search cardinality."""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from app.models.advertisement import Advertisement
from app.models.match import Match
from app.models.outbox_event import OutboxEvent
from app.models.search import Search
from app.services.matching import MatchingService
from datetime import datetime, timezone

pytestmark = pytest.mark.stress


def _seed_matching_searches(session, count: int, *, brand: str = "Toyota") -> None:
    searches = [
        Search(user_id=1, brand=brand, enabled=True, name=f"match-{i}")
        for i in range(count)
    ]
    session.add_all(searches)
    session.commit()


def test_single_ad_matches_many_searches(stress_db_session, stress_scale):
    search_count = stress_scale.matching_searches
    _seed_matching_searches(stress_db_session, search_count)

    ad = Advertisement(
        bama_id="fanout-ad-1",
        url="https://bama.ir/car/detail-fanout-ad-1",
        title="Toyota Camry Fanout",
        brand="Toyota",
        model="Camry",
        year=1400,
        price=2_000_000_000,
        crawled_at=datetime.now(timezone.utc),
    )
    stress_db_session.add(ad)
    stress_db_session.commit()
    stress_db_session.refresh(ad)

    service = MatchingService(stress_db_session)
    matches = service.process_new_ad(ad.id)
    stress_db_session.commit()

    assert len(matches) == search_count

    match_count = stress_db_session.scalar(select(func.count()).select_from(Match))
    assert match_count == search_count

    notify_events = list(
        stress_db_session.scalars(
            select(OutboxEvent).where(OutboxEvent.event_type == "notify.requested")
        )
    )
    assert len(notify_events) == search_count


def test_many_ads_many_searches_unique_constraint(stress_db_session, stress_scale):
    """Process multiple ads against overlapping searches — no duplicate matches."""
    search_count = min(stress_scale.matching_searches, 50)
    ad_count = min(20, stress_scale.crawl_ads // 10)
    _seed_matching_searches(stress_db_session, search_count, brand="Honda")

    ads: list[Advertisement] = []
    now = datetime.now(timezone.utc)
    for i in range(ad_count):
        ad = Advertisement(
            bama_id=f"fanout-multi-{i}",
            url=f"https://bama.ir/car/detail-fanout-multi-{i}",
            title=f"Honda Civic {i}",
            brand="Honda",
            model="Civic",
            year=1398,
            price=1_500_000_000,
            crawled_at=now,
        )
        ads.append(ad)
    stress_db_session.add_all(ads)
    stress_db_session.commit()

    service = MatchingService(stress_db_session)
    total_matches = 0
    for ad in ads:
        stress_db_session.refresh(ad)
        created = service.process_new_ad(ad.id)
        total_matches += len(created)
    stress_db_session.commit()

    expected = search_count * ad_count
    assert total_matches == expected

    match_count = stress_db_session.scalar(select(func.count()).select_from(Match))
    assert match_count == expected

    # Re-processing must not create duplicates
    for ad in ads:
        stress_db_session.refresh(ad)
        again = service.process_new_ad(ad.id)
        assert again == []
    stress_db_session.commit()

    match_count_after = stress_db_session.scalar(select(func.count()).select_from(Match))
    assert match_count_after == expected
