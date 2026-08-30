from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories.site_section_repository import SiteSectionRepository
from config import settings


def resolve_listing_url(session: Session, section: str = "car") -> str:
    """Pick listing URL from site catalog if available, else settings default."""
    sections = SiteSectionRepository(session).list_all()
    for row in sections:
        if row.section_key != section:
            continue
        for pattern in row.url_patterns or []:
            if "listing" in pattern or section in pattern:
                pass
        for root in row.root_urls or []:
            if section in root and "detail" not in root:
                return root.split("?")[0]
        if row.root_urls:
            return row.root_urls[0].split("?")[0]
    return settings.BAMA_LISTING_URL
