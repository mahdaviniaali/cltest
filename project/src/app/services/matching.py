from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.search_filter import ad_matches_search_criteria
from app.models.match import Match
from app.models.search import Search
from app.repositories.advertisement_repository import AdvertisementRepository
from app.repositories.outbox_repository import OutboxRepository
from app.repositories.search_repository import SearchRepository
from config import settings

logger = logging.getLogger(__name__)


class MatchingService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._ads = AdvertisementRepository(session)
        self._searches = SearchRepository(session)
        self._outbox = OutboxRepository(session)

    def process_new_ad(self, ad_id: int) -> list[Match]:
        ad = self._ads.get_by_id(ad_id)
        if ad is None:
            raise ValueError(f"Ad not found: {ad_id}")

        candidates = self._searches.list_candidates_for_ad(ad)
        created: list[Match] = []
        for search in candidates:
            if not self._matches(ad, search):
                continue
            match = self._create_match(ad.id, search.id)
            if match is not None:
                created.append(match)
        return created

    def match_existing_for_search(self, search_id: int) -> list[Match]:
        if not settings.NOTIFY_ON_EXISTING_MATCH:
            return []

        search = self._session.get(Search, search_id)
        if search is None or not search.enabled:
            return []

        ads = self._ads.list_matching_filter(
            brand=search.brand,
            model=search.model,
            min_year=search.min_year,
            max_price=search.max_price,
            max_mileage=search.max_mileage,
            location=search.location,
            limit=1000,
        )
        created: list[Match] = []
        for ad in ads:
            match = self._create_match(ad.id, search.id)
            if match is not None:
                created.append(match)
        self._session.commit()
        return created

    def _matches(self, ad, search: Search) -> bool:
        return ad_matches_search_criteria(
            ad,
            brand=search.brand,
            model=search.model,
            min_year=search.min_year,
            max_price=search.max_price,
            max_mileage=search.max_mileage,
            location=search.location,
        )

    def _create_match(self, ad_id: int, search_id: int) -> Optional[Match]:
        existing = self._session.scalar(
            select(Match).where(Match.ad_id == ad_id, Match.search_id == search_id)
        )
        if existing is not None:
            return None

        match = Match(ad_id=ad_id, search_id=search_id)
        self._session.add(match)
        self._session.flush()

        self._outbox.enqueue(
            event_type="notify.requested",
            aggregate_id=f"{ad_id}:{search_id}",
            payload={"match_id": match.id, "ad_id": ad_id, "search_id": search_id},
        )
        self._session.flush()
        return match
