from __future__ import annotations

import re
from dataclasses import replace
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from crawler.domain.taxonomy_urls import ClassifiedTaxonomyUrl

REVIEW_HUBS = {
    "car": "https://bama.ir/car-reviews",
    "motorcycle": "https://bama.ir/motorcycle-reviews",
    "truck": "https://bama.ir/truck-reviews",
}

_FA_RUN = re.compile(
    r"[\u0600-\u06FF\u200c][\u0600-\u06FF\u200c0-9() ]*[\u0600-\u06FF\u200c0-9)]?"
)
_TITLE_PAIR = re.compile(r'title:\{en:"([^"]+)",fa:"([^"]+)"\}')
_MODEL_PAIR = re.compile(r'brand_model_en:"([^"]+)",brand_model_fa:"([^"]+)"')
_SPECS_SUFFIX = re.compile(r"-specs-.*$", re.I)
_SKIP_TEXTS = frozenset({"بیشتر", "more", "مشاهده همه"})


def bilingual_label(*, fa: str = "", en: str = "", slug: str = "") -> str:
    fa = " ".join(fa.split())
    en = " ".join((en or slug.replace("-", " ")).split())
    en_display = _title_en(en)
    if fa and en_display:
        if en_display.lower() in fa.lower():
            return fa
        return f"{fa} {en_display}"
    return fa or en_display or slug.replace("-", " ")


def apply_review_labels(
    classified: list[ClassifiedTaxonomyUrl],
    html_by_section: dict[str, str | list[str]],
) -> list[ClassifiedTaxonomyUrl]:
    catalogs: dict[str, dict[tuple, tuple[str, str]]] = {}
    for section, html in html_by_section.items():
        catalog: dict[tuple, tuple[str, str]] = {}
        for chunk in _as_html_chunks(html):
            catalog.update(parse_review_labels(chunk))
        if catalog:
            catalogs[section] = catalog
    out: list[ClassifiedTaxonomyUrl] = []
    for item in classified:
        names = lookup_review_names(catalogs.get(item.section) or {}, item)
        if not names:
            out.append(item)
            continue
        fa, en = names
        if not fa.strip():
            out.append(item)
            continue
        out.append(replace(item, label=bilingual_label(fa=fa, en=en, slug=item.slug)))
    return out


def parse_review_labels(html: str) -> dict[tuple, tuple[str, str]]:
    """Map (brand, ...) keys to (fa, en) names parsed from a Bama reviews hub."""
    catalog: dict[tuple, tuple[str, str]] = {}
    soup = BeautifulSoup(html, "lxml")
    for anchor in soup.find_all("a", href=True):
        key = _key_from_review_href(str(anchor["href"]))
        if key is None:
            continue
        text = anchor.get_text(" ", strip=True)
        if not text or text in _SKIP_TEXTS:
            continue
        fa, en = split_bilingual(text)
        if not fa:
            continue
        catalog[key] = (fa, en)

    for en, fa in _TITLE_PAIR.findall(html):
        slug = _slugify_en(en)
        if slug:
            catalog[("brand", slug)] = (fa, en)
    for en, fa in _MODEL_PAIR.findall(html):
        parts = en.strip().split()
        if len(parts) < 2:
            continue
        brand_slug = parts[0].lower()
        model_compact = "".join(parts[1:]).lower()
        model_hyphen = "-".join(parts[1:]).lower()
        catalog[("model", brand_slug, model_compact)] = (fa, en)
        if model_hyphen != model_compact:
            catalog[("model", brand_slug, model_hyphen)] = (fa, en)

    return catalog


def split_bilingual(text: str) -> tuple[str, str]:
    fa_parts = [m.group(0).strip() for m in _FA_RUN.finditer(text)]
    fa = " ".join(p for p in fa_parts if p)
    latin = re.findall(r"[A-Za-z][A-Za-z0-9-]*", text)
    en = " ".join(latin)
    return fa, en


def _title_en(en: str) -> str:
    if not en:
        return ""
    compact = en.replace(" ", "")
    if en.isupper():
        return en if len(compact) <= 4 else en.title()
    if en.islower() and compact.isalpha() and 2 <= len(compact) <= 3:
        return en.upper()
    if en.islower():
        return en[:1].upper() + en[1:]
    return en


def lookup_review_names(catalog: dict[tuple, tuple[str, str]], item: ClassifiedTaxonomyUrl) -> tuple[str, str] | None:
    compact = item.slug.replace("-", "")
    if item.term_type == "brand":
        return catalog.get(("brand", item.slug)) or catalog.get(("brand", compact))
    brand_compact = item.brand_slug.replace("-", "")
    for key in (
        ("model", item.brand_slug, item.slug),
        ("model", item.brand_slug, compact),
        ("model", brand_compact, compact),
    ):
        names = catalog.get(key)
        if names:
            return names
    return None


def _as_html_chunks(html: str | list[str]) -> list[str]:
    if isinstance(html, list):
        return [chunk for chunk in html if chunk]
    return [html] if html else []


def _slugify_en(en: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", en.lower())


def _key_from_review_href(href: str) -> tuple | None:
    parsed = urlparse(href)
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 2 or parts[0] not in {"car-reviews", "motorcycle-reviews", "truck-reviews"}:
        return None
    brand = parts[1].lower()
    if len(parts) == 2:
        return ("brand", brand)
    model = _SPECS_SUFFIX.sub("", parts[2]).lower()
    if not model:
        return None
    return ("model", brand, model)
