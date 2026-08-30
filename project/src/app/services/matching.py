from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.search import Search
from app.repositories.advertisement_repository import AdvertisementRepository
from app.repositories.outbox_repository import OutboxRepository

logger = logging.getLogger(__name__)


class MatchingService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._ads = AdvertisementRepository(session)
        self._outbox = OutboxRepository(session)

    def process_new_ad(self, ad_id: int) -> list[Match]:
        ad = self._ads.get_by_id(ad_id)
        if ad is None:
            raise ValueError(f"Ad not found: {ad_id}")

        enabled_searches = list(
            self._session.scalars(select(Search).where(Search.enabled.is_(True)))
        )
        created: list[Match] = []
        for search in enabled_searches:
            if not self._matches(ad, search):
                continue
            match = self._create_match(ad.id, search.id)
            if match is not None:
                created.append(match)
        return created

    def _matches(self, ad, search: Search) -> bool:
        if search.brand and ad.brand and search.brand != ad.brand:
            return False
        if search.model and ad.model and search.model != ad.model:
            return False
        if search.min_year is not None and ad.year is not None and ad.year < search.min_year:
            return False
        if search.max_price is not None and ad.price is not None and ad.price > search.max_price:
            return False
        if search.max_mileage is not None and ad.mileage is not None and ad.mileage > search.max_mileage:
            return False
        if search.location and ad.location and search.location not in ad.location:
            return False
        return True

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
