from typing import Any, Optional

from sqlalchemy import select
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

    def exists(self, bama_id: str) -> bool:
        return self.get_by_bama_id(bama_id) is not None

    def save_new(self, data: dict[str, Any]) -> tuple[Advertisement, bool]:
        """Insert if bama_id is new. Returns (record, created)."""
        existing = self.get_by_bama_id(data["bama_id"])
        if existing is not None:
            return existing, False

        advertisement = Advertisement(**data)
        self._session.add(advertisement)
        self._session.commit()
        self._session.refresh(advertisement)
        return advertisement, True

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

    def list_active(self, limit: int = 100) -> list[Advertisement]:
        stmt = (
            select(Advertisement)
            .where(
                Advertisement.is_deleted.is_(False),
                Advertisement.is_sold.is_(False),
            )
            .order_by(Advertisement.crawled_at.desc())
            .limit(limit)
        )
        return list(self._session.scalars(stmt))
