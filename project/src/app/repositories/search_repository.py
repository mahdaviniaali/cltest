from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

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
