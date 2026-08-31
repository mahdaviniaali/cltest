from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.domain.filter_fingerprint import FilterFingerprint, compute_filter_fingerprint
from app.models.filter_crawl_state import FilterCrawlState
from app.models.search import Search


class FilterCrawlStateRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, fingerprint: str) -> Optional[FilterCrawlState]:
        return self._session.get(FilterCrawlState, fingerprint)

    def get_for_search(self, search: Search) -> Optional[FilterCrawlState]:
        if not search.filter_fingerprint:
            return None
        return self.get(search.filter_fingerprint)

    def upsert_from_search(
        self,
        search: Search,
        *,
        listing_url: str,
        fingerprint: FilterFingerprint,
    ) -> FilterCrawlState:
        row = self.get(fingerprint.fingerprint)
        if row is None:
            row = FilterCrawlState(
                fingerprint=fingerprint.fingerprint,
                section_key=fingerprint.canonical["section_key"],
                listing_url=listing_url,
                brand=fingerprint.canonical.get("brand"),
                model=fingerprint.canonical.get("model"),
                min_year=fingerprint.canonical.get("min_year"),
                max_price=fingerprint.canonical.get("max_price"),
                max_mileage=fingerprint.canonical.get("max_mileage"),
                location=fingerprint.canonical.get("location"),
            )
            self._session.add(row)
        else:
            row.listing_url = listing_url
            row.section_key = fingerprint.canonical["section_key"]
            row.brand = fingerprint.canonical.get("brand")
            row.model = fingerprint.canonical.get("model")
            row.min_year = fingerprint.canonical.get("min_year")
            row.max_price = fingerprint.canonical.get("max_price")
            row.max_mileage = fingerprint.canonical.get("max_mileage")
            row.location = fingerprint.canonical.get("location")
        self._session.flush()
        return row

    def update_checkpoint(
        self,
        fingerprint: str,
        *,
        last_seen_bama_id: str,
        job_id: str,
        listing_url: Optional[str] = None,
    ) -> None:
        row = self.get(fingerprint)
        if row is None:
            return
        row.last_seen_bama_id = last_seen_bama_id
        row.last_job_id = job_id
        row.last_crawl_at = datetime.now(timezone.utc)
        if listing_url:
            row.listing_url = listing_url
        self._session.flush()

    def touch_crawl(self, fingerprint: str, *, job_id: str) -> None:
        row = self.get(fingerprint)
        if row is None:
            return
        row.last_job_id = job_id
        row.last_crawl_at = datetime.now(timezone.utc)
        self._session.flush()

    def refresh_enabled_counts(self) -> None:
        counts = dict(
            self._session.execute(
                select(Search.filter_fingerprint, func.count())
                .where(Search.enabled.is_(True))
                .where(Search.filter_fingerprint.isnot(None))
                .group_by(Search.filter_fingerprint)
            ).all()
        )
        self._session.execute(update(FilterCrawlState).values(enabled_search_count=0))
        for fingerprint, count in counts.items():
            row = self.get(fingerprint)
            if row is not None:
                row.enabled_search_count = int(count)
        self._session.flush()

    def list_active(self, *, limit: int = 200) -> list[FilterCrawlState]:
        self.refresh_enabled_counts()
        stmt = (
            select(FilterCrawlState)
            .where(FilterCrawlState.enabled_search_count > 0)
            .order_by(FilterCrawlState.last_crawl_at.asc().nullsfirst())
            .limit(limit)
        )
        return list(self._session.scalars(stmt).all())

    def list_stale_active(self, *, max_age_seconds: int, limit: int = 50) -> list[FilterCrawlState]:
        self.refresh_enabled_counts()
        cutoff = datetime.now(timezone.utc).timestamp() - max_age_seconds
        rows = self.list_active(limit=limit * 4)
        stale: list[FilterCrawlState] = []
        for row in rows:
            if row.last_crawl_at is None:
                stale.append(row)
                continue
            ts = row.last_crawl_at
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ts.timestamp() <= cutoff:
                stale.append(row)
        stale.sort(
            key=lambda r: (
                -r.enabled_search_count,
                r.last_crawl_at.timestamp() if r.last_crawl_at is not None else float("-inf"),
            )
        )
        return stale[:limit]

    def ensure_fingerprint_on_search(self, search: Search, listing_url: str) -> FilterFingerprint:
        fp = compute_filter_fingerprint(
            section_key=search.section_key,
            brand=search.brand,
            model=search.model,
            brand_term_id=search.brand_term_id,
            model_term_id=search.model_term_id,
            min_year=search.min_year,
            max_price=search.max_price,
            max_mileage=search.max_mileage,
            location=search.location,
        )
        search.filter_fingerprint = fp.fingerprint
        self.upsert_from_search(search, listing_url=listing_url, fingerprint=fp)
        return fp
