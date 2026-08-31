from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

VEHICLE_SECTIONS = ("car", "motorcycle", "truck")
RESERVED_SLUGS = frozenset(
    {
        "all",
        "compare",
        "price",
        "news",
        "market",
        "reviews",
        "detail",
        "new",
        "used",
        "search",
        "filters",
        "filter",
        "dealer",
    }
)


@dataclass(frozen=True, slots=True)
class ClassifiedTaxonomyUrl:
    section: str
    term_type: str
    slug: str
    brand_slug: str
    listing_url: str
    label: str
    parent_listing_url: str | None = None


def path_parts(url: str) -> list[str]:
    return [p for p in urlparse(url).path.split("/") if p]


def canonical_listing_url(url: str) -> str | None:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    parts = [p for p in parsed.path.split("/") if p]
    if not parts:
        return None
    return f"https://{host}/{'/'.join(parts)}"


def _skip_slug(slug: str) -> bool:
    if not slug or slug.lower() in RESERVED_SLUGS:
        return True
    return slug.lower().startswith("detail-")


def _label(slug: str) -> str:
    return slug.replace("-", " ").strip() or slug


def _looks_like_location(slug: str) -> bool:
    """Bama city/province slugs use underscores, e.g. azarbaijan_sharghi-tabriz."""
    return "_" in slug


def classify_taxonomy_urls(urls: list[str]) -> list[ClassifiedTaxonomyUrl]:
    """Split Bama listing URLs into brand/model catalog entries.

    Bama publishes both nested paths (``/car/porsche/panamera``) and
    hyphenated listing paths (``/car/porsche-panamera``). Classification
    uses URL shape, not crawl depth.
    """
    two_part: dict[tuple[str, str], str] = {}
    nested_models: list[tuple[str, str, str, str]] = []

    for raw in urls:
        listing = canonical_listing_url(raw)
        if listing is None:
            continue
        parts = path_parts(listing)
        if len(parts) < 2:
            continue
        section = parts[0].lower()
        if section not in VEHICLE_SECTIONS:
            continue
        if len(parts) == 2:
            slug = parts[1]
            if _skip_slug(slug):
                continue
            two_part[(section, slug)] = listing
        elif len(parts) >= 3:
            brand_slug, model_slug = parts[1], parts[2]
            if _skip_slug(brand_slug) or _skip_slug(model_slug) or _looks_like_location(model_slug):
                continue
            nested_models.append((section, brand_slug, model_slug, listing))

    out: list[ClassifiedTaxonomyUrl] = []
    seen: set[tuple[str, str, str]] = set()

    for section in VEHICLE_SECTIONS:
        slugs = {slug for (sec, slug) in two_part if sec == section}
        model_slugs = {
            slug
            for slug in slugs
            if any(slug.startswith(other + "-") for other in slugs if other != slug)
        }
        brand_slugs = slugs - model_slugs
        for section_key, brand_slug, model_slug, listing in nested_models:
            if section_key == section:
                brand_slugs.add(brand_slug)

        for slug in sorted(brand_slugs):
            listing = two_part.get((section, slug)) or f"https://bama.ir/{section}/{slug}"
            key = (section, "brand", slug)
            if key in seen:
                continue
            seen.add(key)
            out.append(
                ClassifiedTaxonomyUrl(
                    section=section,
                    term_type="brand",
                    slug=slug,
                    brand_slug=slug,
                    listing_url=listing,
                    label=_label(slug),
                )
            )

        for slug in sorted(model_slugs):
            parents = [b for b in brand_slugs if slug.startswith(b + "-")]
            if not parents:
                continue
            parent = max(parents, key=len)
            model_slug = slug[len(parent) + 1 :]
            if not model_slug:
                continue
            listing = two_part[(section, slug)]
            key = (section, "model", f"{parent}/{model_slug}")
            if key in seen:
                continue
            seen.add(key)
            parent_listing = two_part.get((section, parent)) or f"https://bama.ir/{section}/{parent}"
            out.append(
                ClassifiedTaxonomyUrl(
                    section=section,
                    term_type="model",
                    slug=model_slug,
                    brand_slug=parent,
                    listing_url=listing,
                    label=_label(model_slug),
                    parent_listing_url=parent_listing,
                )
            )

        for nested_section, brand_slug, model_slug, listing in nested_models:
            if nested_section != section:
                continue
            key = (section, "model", f"{brand_slug}/{model_slug}")
            if key in seen:
                continue
            seen.add(key)
            parent_listing = two_part.get((section, brand_slug)) or f"https://bama.ir/{section}/{brand_slug}"
            out.append(
                ClassifiedTaxonomyUrl(
                    section=section,
                    term_type="model",
                    slug=model_slug,
                    brand_slug=brand_slug,
                    listing_url=listing,
                    label=_label(model_slug),
                    parent_listing_url=parent_listing,
                )
            )

    return out
