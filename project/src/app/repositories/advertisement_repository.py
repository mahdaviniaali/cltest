from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.advertisement import Advertisement


class AdvertisementRepository:
    """Persistence port for Bama.ir advertisements."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_bama_id(self, bama_id: str) -> Optional[Advertisement]:
        return self._session.scalar(
            select(Advertisement).where(Advertisement.bama_id == bama_id)
        )

    def get_by_id(self, ad_id: int) -> Optional[Advertisement]:
        return self._session.get(Advertisement, ad_id)

    def exists(self, bama_id: str) -> bool:
        return self.get_by_bama_id(bama_id) is not None

    def add_new(self, data: dict[str, Any]) -> tuple[Advertisement, bool]:
        """Stage a new ad in the session. Caller commits via UnitOfWork."""
        existing = self.get_by_bama_id(data["bama_id"])
        if existing is not None:
            return existing, False

        advertisement = Advertisement(**data)
        self._session.add(advertisement)
        self._session.flush()
        return advertisement, True

    def save_new(self, data: dict[str, Any]) -> tuple[Advertisement, bool]:
        """Insert if bama_id is new. Commits immediately (legacy API paths)."""
        ad, created = self.add_new(data)
        if created:
            self._session.commit()
            self._session.refresh(ad)
        return ad, created

    def update_status(
        self,
        bama_id: str,
        *,
        is_deleted: Optional[bool] = None,
        is_sold: Optional[bool] = None,
    ) -> Optional[Advertisement]:
        advertisement = self.get_by_bama_id(bama_id)
        if advertisement is None:
            return None

        if is_deleted is not None:
            advertisement.is_deleted = is_deleted
        if is_sold is not None:
            advertisement.is_sold = is_sold

        self._session.commit()
        self._session.refresh(advertisement)
        return advertisement

    def list_active(self, limit: int = 100, offset: int = 0) -> list[Advertisement]:
        stmt = (
            select(Advertisement)
            .where(
                Advertisement.is_deleted.is_(False),
                Advertisement.is_sold.is_(False),
            )
            .order_by(Advertisement.crawled_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self._session.scalars(stmt))

    def list_matching_filter(
        self,
        *,
        brand: Optional[str] = None,
        model: Optional[str] = None,
        min_year: Optional[int] = None,
        max_price: Optional[int] = None,
        max_mileage: Optional[int] = None,
        location: Optional[str] = None,
        limit: int = 100,
    ) -> list[Advertisement]:
        stmt = select(Advertisement).where(
            Advertisement.is_deleted.is_(False),
            Advertisement.is_sold.is_(False),
        )
        if brand:
            stmt = stmt.where(func.lower(Advertisement.brand) == brand.lower())
        if model:
            stmt = stmt.where(func.lower(Advertisement.model) == model.lower())
        if min_year is not None:
            stmt = stmt.where(Advertisement.year >= min_year)
        if max_price is not None:
            stmt = stmt.where(Advertisement.price <= max_price)
        if max_mileage is not None:
            stmt = stmt.where(Advertisement.mileage <= max_mileage)
        if location:
            stmt = stmt.where(Advertisement.location.ilike(f"%{location}%"))

        stmt = stmt.order_by(Advertisement.crawled_at.desc()).limit(limit)
        return list(self._session.scalars(stmt))
