from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.advertisement import Advertisement
from app.repositories.taxonomy_repository import TaxonomyRepository
from crawler.application.taxonomy_builder import VEHICLE_SECTIONS


class CityTaxonomySync:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._taxonomy = TaxonomyRepository(session)

    def sync(self) -> int:
        locations = [
            loc.strip()
            for loc in self._session.scalars(
                select(Advertisement.location)
                .where(Advertisement.location.isnot(None))
                .where(Advertisement.location != "")
                .distinct()
                .order_by(Advertisement.location)
            ).all()
            if loc and loc.strip()
        ]
        if not locations:
            return 0
        snapshot = self._taxonomy.get_or_create_city_snapshot()
        added = 0
        for section in VEHICLE_SECTIONS:
            added += self._taxonomy.sync_cities(
                snapshot_id=snapshot.id,
                section_key=section,
                cities=locations,
            )
        self._session.flush()
        return added

    def list_cities(self, *, section_key: str) -> list[str]:
        terms = self._taxonomy.list_terms(section_key=section_key, term_type="city")
        if not terms:
            self.sync()
            terms = self._taxonomy.list_terms(section_key=section_key, term_type="city")
        return [t.label for t in terms]
