from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import func, select, update

from app.models.taxonomy import TaxonomyRef, TaxonomySnapshot, TaxonomyTerm


class TaxonomyRepository:
    SCHEMA_VERSION = 1

    def __init__(self, session) -> None:
        self._session = session

    def create_snapshot(self, *, source_job_id: Optional[str]) -> TaxonomySnapshot:
        self._session.execute(update(TaxonomySnapshot).values(is_current=False))
        snapshot = TaxonomySnapshot(
            source_job_id=source_job_id,
            schema_version=self.SCHEMA_VERSION,
            is_current=True,
        )
        self._session.add(snapshot)
        self._session.flush()
        self._session.execute(
            update(TaxonomyTerm)
            .where(TaxonomyTerm.term_type.in_(["brand", "model"]))
            .values(is_active=False)
        )
        self._session.flush()
        return snapshot

    def add_term(
        self,
        *,
        snapshot_id: int,
        section_key: str,
        term_type: str,
        label: str,
        slug: str,
        listing_url: Optional[str],
        page_key: Optional[str],
        parent_id: Optional[int] = None,
        meta: Optional[dict[str, Any]] = None,
    ) -> TaxonomyTerm:
        term = TaxonomyTerm(
            snapshot_id=snapshot_id,
            section_key=section_key,
            term_type=term_type,
            parent_id=parent_id,
            label=label,
            slug=slug,
            listing_url=listing_url,
            page_key=page_key,
            is_active=True,
            meta=meta,
        )
        self._session.add(term)
        self._session.flush()
        return term

    def add_ref(
        self,
        *,
        term_id: int,
        page_key: Optional[str],
        url: str,
        url_pattern: Optional[str],
        source_job_id: Optional[str],
    ) -> TaxonomyRef:
        ref = TaxonomyRef(
            term_id=term_id,
            page_key=page_key,
            url=url,
            url_pattern=url_pattern,
            source_job_id=source_job_id,
            extracted_at=datetime.now(timezone.utc),
        )
        self._session.add(ref)
        self._session.flush()
        return ref

    def get_term(self, term_id: int) -> Optional[TaxonomyTerm]:
        return self._session.get(TaxonomyTerm, term_id)

    def list_terms(
        self,
        *,
        section_key: Optional[str] = None,
        term_type: Optional[str] = None,
        parent_id: Optional[int] = None,
        active_only: bool = True,
        limit: int = 10_000,
    ) -> list[TaxonomyTerm]:
        stmt = select(TaxonomyTerm).order_by(TaxonomyTerm.label).limit(limit)
        if section_key:
            stmt = stmt.where(TaxonomyTerm.section_key == section_key)
        if term_type:
            stmt = stmt.where(TaxonomyTerm.term_type == term_type)
        if parent_id is not None:
            stmt = stmt.where(TaxonomyTerm.parent_id == parent_id)
        if active_only:
            stmt = stmt.where(TaxonomyTerm.is_active.is_(True))
        return list(self._session.scalars(stmt).all())

    def find_term_by_slug(
        self,
        *,
        section_key: str,
        term_type: str,
        slug: str,
        parent_id: Optional[int] = None,
        active_only: bool = True,
    ) -> Optional[TaxonomyTerm]:
        stmt = select(TaxonomyTerm).where(
            TaxonomyTerm.section_key == section_key,
            TaxonomyTerm.term_type == term_type,
            TaxonomyTerm.slug == slug,
        )
        if parent_id is not None:
            stmt = stmt.where(TaxonomyTerm.parent_id == parent_id)
        if active_only:
            stmt = stmt.where(TaxonomyTerm.is_active.is_(True))
        return self._session.scalar(stmt)

    def count_terms_by_section(self, *, term_type: str, active_only: bool = True) -> dict[str, int]:
        stmt = (
            select(TaxonomyTerm.section_key, func.count())
            .where(TaxonomyTerm.term_type == term_type)
            .group_by(TaxonomyTerm.section_key)
        )
        if active_only:
            stmt = stmt.where(TaxonomyTerm.is_active.is_(True))
        return dict(self._session.execute(stmt).all())

    def count_active_terms(self, *, term_type: Optional[str] = None) -> int:
        stmt = select(func.count()).select_from(TaxonomyTerm).where(TaxonomyTerm.is_active.is_(True))
        if term_type:
            stmt = stmt.where(TaxonomyTerm.term_type == term_type)
        return int(self._session.scalar(stmt) or 0)

    def count_stale_terms(self, *, term_type: Optional[str] = None) -> int:
        stmt = select(func.count()).select_from(TaxonomyTerm).where(TaxonomyTerm.is_active.is_(False))
        if term_type:
            stmt = stmt.where(TaxonomyTerm.term_type == term_type)
        return int(self._session.scalar(stmt) or 0)

    def get_current_snapshot(self) -> Optional[TaxonomySnapshot]:
        return self._session.scalar(
            select(TaxonomySnapshot).where(TaxonomySnapshot.is_current.is_(True)).limit(1)
        )

    def sync_cities(
        self,
        *,
        snapshot_id: int,
        section_key: str,
        cities: list[str],
    ) -> int:
        self._session.execute(
            update(TaxonomyTerm)
            .where(
                TaxonomyTerm.section_key == section_key,
                TaxonomyTerm.term_type == "city",
            )
            .values(is_active=False)
        )
        added = 0
        for city in cities:
            if not city or not city.strip():
                continue
            label = city.strip()
            slug = label.lower().replace(" ", "-")
            self.add_term(
                snapshot_id=snapshot_id,
                section_key=section_key,
                term_type="city",
                label=label,
                slug=slug,
                listing_url=None,
                page_key=None,
                meta={"source": "advertisements"},
            )
            added += 1
        self._session.flush()
        return added

    def get_or_create_city_snapshot(self) -> TaxonomySnapshot:
        current = self.get_current_snapshot()
        if current is not None:
            return current
        return self.create_snapshot(source_job_id=None)
