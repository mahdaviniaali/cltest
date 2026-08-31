from __future__ import annotations

import re
from typing import Optional
from urllib.parse import urljoin, urlparse, urlencode, parse_qs, urlunparse

from bs4 import BeautifulSoup

from crawler.domain.labels import normalize_label
from crawler.domain.entities import AdDraft, ListingCard

BAMA_BASE = "https://bama.ir"

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

        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            match = detail_re.search(href)
            if not match:
                continue
            bama_id = match.group("id")
            if bama_id in seen:
                continue
            seen.add(bama_id)
            url = urljoin(BAMA_BASE, href)
            title = anchor.get_text(" ", strip=True) or f"Ad {bama_id}"
            cards.append(ListingCard(bama_id=bama_id, url=url, title=title))

        return cards

    def next_page_url(self, current_url: str, page: int) -> str:
        parsed = urlparse(current_url)
        query = parse_qs(parsed.query)
        query["page"] = [str(page)]
        new_query = urlencode({k: v[0] for k, v in query.items()})
        if not parsed.query and page == 1:
            return current_url
        base = urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))
        if page <= 1:
            return base or self._listing_url
        return f"{base}?{new_query}" if new_query else f"{base}?page={page}"


class BamaDetailParser:
    def parse(self, html: str, *, url: str, bama_id: str) -> AdDraft:
        soup = BeautifulSoup(html, "lxml")
        title_el = soup.find("h1")
        title = title_el.get_text(strip=True) if title_el else f"Ad {bama_id}"

        brand, model = self._split_title(title)
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

    def _split_title(self, title: str) -> tuple[str | None, str | None]:
        parts = title.split()
        if len(parts) >= 2:
            return normalize_label(parts[0]), normalize_label(parts[1])
        if parts:
            return normalize_label(parts[0]), None
        return None, None

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
