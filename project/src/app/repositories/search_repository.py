from typing import Any, Optional

from sqlalchemy import func, literal, or_, select
from sqlalchemy.orm import Session

from app.domain.search_filter import normalize_for_match
from app.models.advertisement import Advertisement
from app.models.search import Search


class SearchRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_for_user(self, user_id: int) -> list[Search]:
        stmt = (
            select(Search)
            .where(Search.user_id == user_id)
            .order_by(Search.created_at.desc())
        )
        return list(self._session.scalars(stmt))

    def get_for_user(self, user_id: int, search_id: int) -> Optional[Search]:
        return self._session.scalar(
            select(Search).where(Search.id == search_id, Search.user_id == user_id)
        )

    def create(self, user_id: int, data: dict[str, Any]) -> Search:
        search = Search(user_id=user_id, **data)
        self._session.add(search)
        self._session.commit()
        self._session.refresh(search)
        return search

    def update(self, search: Search, data: dict[str, Any]) -> Search:
        for key, value in data.items():
            setattr(search, key, value)
        self._session.commit()
        self._session.refresh(search)
        return search

    def delete(self, search: Search) -> None:
        self._session.delete(search)
        self._session.commit()

    def toggle_enabled(self, search: Search) -> Search:
        search.enabled = not search.enabled
        self._session.commit()
        self._session.refresh(search)
        return search

    def list_enabled_by_fingerprint(self, fingerprint: str) -> list[Search]:
        stmt = select(Search).where(
            Search.filter_fingerprint == fingerprint,
            Search.enabled.is_(True),
        )
        return list(self._session.scalars(stmt))

    def list_enabled_by_brand_term(self, brand_term_id: int) -> list[Search]:
        stmt = select(Search).where(
            Search.brand_term_id == brand_term_id,
            Search.enabled.is_(True),
        )
        return list(self._session.scalars(stmt))

    def list_enabled_by_brand(self, brand: str) -> list[Search]:
        stmt = select(Search).where(
            Search.brand == brand,
            Search.enabled.is_(True),
        )
        return list(self._session.scalars(stmt))

    def list_candidates_for_ad(self, ad: Advertisement) -> list[Search]:
        """SQL pre-filter for enabled searches that might match an ad."""
        stmt = select(Search).where(Search.enabled.is_(True))

        if ad.year is not None:
            stmt = stmt.where(or_(Search.min_year.is_(None), Search.min_year <= ad.year))
        if ad.price is not None:
            stmt = stmt.where(or_(Search.max_price.is_(None), Search.max_price >= ad.price))
        if ad.mileage is not None:
            stmt = stmt.where(or_(Search.max_mileage.is_(None), Search.max_mileage >= ad.mileage))

        if ad.location:
            ad_loc = ad.location.lower()
            stmt = stmt.where(
                or_(
                    Search.location.is_(None),
                    literal(ad_loc).like(func.concat("%", func.lower(Search.location), "%")),
                )
            )

        if ad.brand:
            brand_col = func.replace(func.replace(func.lower(literal(ad.brand)), "،", ""), ",", "")
            norm = normalize_for_match(ad.brand)
            if norm:
                search_brand_col = func.replace(
                    func.replace(func.lower(Search.brand), "،", ""), ",", ""
                )
                stmt = stmt.where(
                    or_(
                        Search.brand.is_(None),
                        search_brand_col == norm,
                        search_brand_col.like(f"%{norm}%"),
                        brand_col.like(func.concat("%", search_brand_col, "%")),
                    )
                )

        if ad.model or ad.title:
            model_col = func.replace(func.replace(func.lower(literal(ad.model or "")), "،", ""), ",", "")
            title_col = func.lower(literal(ad.title or ""))
            norm_model = normalize_for_match(ad.model)
            if norm_model:
                search_model_col = func.replace(
                    func.replace(func.lower(Search.model), "،", ""), ",", ""
                )
                search_title_match = or_(
                    model_col.like(func.concat("%", search_model_col, "%")),
                    title_col.like(func.concat("%", search_model_col, "%")),
                    search_model_col.like(f"%{norm_model}%"),
                )
                stmt = stmt.where(or_(Search.model.is_(None), search_title_match))

        return list(self._session.scalars(stmt))
