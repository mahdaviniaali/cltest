"""Synthetic Bama-shaped HTML for stress tests — no live network."""

from __future__ import annotations

from urllib.parse import urlencode, urlparse, urlunparse

BAMA_BASE = "https://bama.ir"
DEFAULT_LISTING_URL = f"{BAMA_BASE}/car"


def listing_page_url(listing_url: str, page: int) -> str:
    parsed = urlparse(listing_url)
    if page <= 1:
        return listing_url
    query = urlencode({"page": str(page)})
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", query, ""))


def make_listing_html(cards: list[tuple[str, str, str]]) -> str:
    """Build listing HTML from (bama_id, url, title) tuples."""
    anchors = "\n".join(
        f'  <a href="{url.replace(BAMA_BASE, "")}">{title}</a>'
        for _bama_id, url, title in cards
    )
    return f"<html><body>\n{anchors}\n</body></html>"


def make_detail_html(
    bama_id: str,
    title: str,
    *,
    brand: str = "Toyota",
    price: int = 1_500_000_000,
    mileage: int = 80_000,
    location: str = "تهران، ایران",
    year: int = 1400,
) -> str:
    return f"""<html><body>
  <h1>{title} {year}</h1>
  <p>{price:,} تومان</p>
  <p>{mileage:,} کیلومتر</p>
  <p>{location}</p>
  <p>{brand}</p>
  <span>detail-{bama_id}</span>
</body></html>"""


def build_crawl_dataset(
    total_ads: int,
    *,
    cards_per_page: int = 20,
    listing_url: str = DEFAULT_LISTING_URL,
    brand: str = "Toyota",
    model_slug: str = "camry",
) -> tuple[dict[str, str], dict[str, str]]:
    """Return (listing_pages, detail_pages) keyed by full URL."""
    pages: dict[str, str] = {}
    details: dict[str, str] = {}

    if total_ads <= 0:
        return pages, details

    page_count = (total_ads + cards_per_page - 1) // cards_per_page
    for page_num in range(1, page_count + 1):
        start = (page_num - 1) * cards_per_page
        end = min(start + cards_per_page, total_ads)
        cards: list[tuple[str, str, str]] = []
        for i in range(start, end):
            bama_id = f"stress-{i:06d}-{brand.lower()}-{model_slug}"
            path = f"/car/detail-{bama_id}"
            url = f"{BAMA_BASE}{path}"
            title = f"{brand} {model_slug.title()} {i}"
            cards.append((bama_id, url, title))
            details[url] = make_detail_html(bama_id, title, brand=brand)
        pages[listing_page_url(listing_url, page_num)] = make_listing_html(cards)

    return pages, details
