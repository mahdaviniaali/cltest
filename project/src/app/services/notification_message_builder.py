from __future__ import annotations

from app.domain.notification_ports import NotificationMessage
from app.models.advertisement import Advertisement
from app.models.search import Search


def _fmt_price(price: int | None) -> str:
    if price is None:
        return "—"
    return f"{price:,}"


def _fmt_mileage(mileage: int | None) -> str:
    if mileage is None:
        return "—"
    return f"{mileage:,} km"


class NotificationMessageBuilder:
    def build(self, ad: Advertisement, search: Search) -> NotificationMessage:
        title = ad.title or f"{ad.brand or ''} {ad.model or ''}".strip() or "آگهی جدید"
        body_lines = [
            f"فیلتر: {search.name or search.brand or 'جستجو'}",
            f"قیمت: {_fmt_price(ad.price)}",
            f"کارکرد: {_fmt_mileage(ad.mileage)}",
        ]
        if ad.location:
            body_lines.append(f"شهر: {ad.location}")
        body = "\n".join(body_lines)
        return NotificationMessage(
            title=title,
            body=body,
            ad_url=ad.url,
            ad_id=ad.id,
            search_id=search.id,
            search_name=search.name,
            extra={
                "bama_id": ad.bama_id,
                "brand": ad.brand,
                "model": ad.model,
                "year": ad.year,
            },
        )
