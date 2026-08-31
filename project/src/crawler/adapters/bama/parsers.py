from __future__ import annotations

import re
from typing import Optional
from urllib.parse import urljoin, urlparse, urlencode, parse_qs, urlunparse

from bs4 import BeautifulSoup

from crawler.domain.labels import normalize_label
from crawler.domain.entities import AdDraft, ListingCard

BAMA_BASE = "https://bama.ir"


def split_bama_title(title: str) -> tuple[str | None, str | None]:
    """Bama H1 is `brand، model` (Persian or ASCII comma). Fallback: first two words."""
    normalized = title.replace("،", ",")
    if "," in normalized:
        left, right = normalized.split(",", 1)
        brand = normalize_label(left)
        model = normalize_label(right)
        if brand and model:
            return brand, model
    parts = title.split()
    if len(parts) >= 2:
        return normalize_label(parts[0]), normalize_label(parts[1])
    if parts:
        return normalize_label(parts[0]), None
    return None, None

DETAIL_PATTERNS = {
    "car": re.compile(r"/car/detail-(?P<id>[a-z0-9-]+)", re.I),
    "motorcycle": re.compile(r"/motorcycle/detail-(?P<id>[a-z0-9-]+)", re.I),
    "truck": re.compile(r"/truck/detail-(?P<id>[a-z0-9-]+)", re.I),
}


def _pattern_for_url(url: str) -> re.Pattern[str]:
    path = urlparse(url).path.lower()
    for section, pattern in DETAIL_PATTERNS.items():
        if f"/{section}" in path:
            return pattern
    return DETAIL_PATTERNS["car"]


class BamaListingParser:
    def __init__(self, listing_url: Optional[str] = None) -> None:
        self._listing_url = listing_url or f"{BAMA_BASE}/car"

    def parse(self, html: str, *, page: int) -> list[ListingCard]:
        soup = BeautifulSoup(html, "lxml")
        cards: list[ListingCard] = []
        seen: set[str] = set()
        detail_re = _pattern_for_url(self._listing_url)
        titles_by_id: dict[str, str] = {}

        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            match = detail_re.search(href)
            if not match:
                continue
            bama_id = match.group("id")
            title = anchor.get_text(" ", strip=True)
            if title:
                titles_by_id[bama_id] = title

        for match in detail_re.finditer(html):
            bama_id = match.group("id")
            if bama_id in seen:
                continue
            seen.add(bama_id)
            path = match.group(0)
            url = urljoin(BAMA_BASE, path)
            title = titles_by_id.get(bama_id) or f"Ad {bama_id}"
            cards.append(ListingCard(bama_id=bama_id, url=url, title=title))

        return cards

    def next_page_url(self, current_url: str, page: int) -> str:
        parsed = urlparse(current_url)
        query = parse_qs(parsed.query)
        if page > 1:
            query["page"] = [str(page)]
        else:
            query.pop("page", None)
        new_query = urlencode({k: v[0] for k, v in query.items()})
        base = urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))
        if new_query:
            return f"{base}?{new_query}"
        return base


class BamaDetailParser:
    def parse(self, html: str, *, url: str, bama_id: str) -> AdDraft:
        soup = BeautifulSoup(html, "lxml")
        title_el = soup.find("h1")
        title = title_el.get_text(strip=True) if title_el else f"Ad {bama_id}"

        brand, model = split_bama_title(title)
        specs = self._extract_specs(soup)
        section = self._section_from_url(url)

        return AdDraft(
            bama_id=bama_id,
            url=url,
            title=title,
            brand=brand,
            model=model,
            year=specs.get("year"),
            price=specs.get("price"),
            mileage=specs.get("mileage"),
            location=specs.get("location"),
            description=specs.get("description"),
            raw_data={"title": title, "section": section, **specs},
        )

    def _section_from_url(self, url: str) -> str:
        path = urlparse(url).path.lower()
        for section in DETAIL_PATTERNS:
            if f"/{section}/" in path:
                return section
        return "car"

    def _extract_specs(self, soup: BeautifulSoup) -> dict:
        out: dict = {}
        text = soup.get_text("\n", strip=True)

        year_match = re.search(r"(13|14)\d{2}", text)
        if year_match:
            out["year"] = int(year_match.group())

        price_match = re.search(r"([\d,]+)\s*تومان", text)
        if price_match:
            out["price"] = int(price_match.group(1).replace(",", ""))

        mileage_match = re.search(r"([\d,]+)\s*کیلومتر", text)
        if mileage_match:
            out["mileage"] = int(mileage_match.group(1).replace(",", ""))

        for line in text.splitlines():
            if "،" in line and len(line) < 80:
                out.setdefault("location", line.strip())
                break

        desc = soup.find("div", class_=re.compile(r"description", re.I))
        if desc:
            out["description"] = desc.get_text(strip=True)

        return out
