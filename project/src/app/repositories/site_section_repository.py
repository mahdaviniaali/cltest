from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.site_map import SiteSection


class SiteSectionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert(
        self,
        *,
        section_key: str,
        label: str,
        root_urls: list[str],
        url_patterns: list[str],
        page_count: int,
        useful_score: float,
    ) -> SiteSection:
        row = self._session.get(SiteSection, section_key)
        now = datetime.now(timezone.utc)
        if row is None:
            row = SiteSection(
                section_key=section_key,
                label=label,
                root_urls=root_urls,
                url_patterns=url_patterns,
                page_count=page_count,
                useful_score=useful_score,
                updated_at=now,
            )
            self._session.add(row)
        else:
            row.label = label
            row.root_urls = root_urls
            row.url_patterns = url_patterns
            row.page_count = page_count
            row.useful_score = useful_score
            row.updated_at = now
        self._session.flush()
        return row

    def list_all(self) -> list[SiteSection]:
        return list(self._session.query(SiteSection).order_by(SiteSection.useful_score.desc()).all())

    def clear_all(self) -> None:
        self._session.query(SiteSection).delete()
        self._session.flush()
