from __future__ import annotations

from crawler.domain.taxonomy_labels import apply_review_labels, bilingual_label, parse_review_labels
from crawler.domain.taxonomy_urls import classify_taxonomy_urls

_REVIEWS_HTML = """
<html><body>
<a href="/car-reviews/pride">pride پراید</a>
<a href="/car-reviews/pride/111-specs-1">pride 111 پراید 111</a>
<a href="/car-reviews/bmw">bmw ب ام و</a>
<a href="/car-reviews/toyota">toyota تویوتا</a>
<a href="/car-reviews/porsche">porsche</a>
<script>
window.__NUXT__={title:{en:"PRIDE",fa:"پراید"},brand_model_en:"pride 111",brand_model_fa:"پراید 111"}
</script>
</body></html>
"""


def test_parse_review_labels_reads_anchors_and_nuxt():
    catalog = parse_review_labels(_REVIEWS_HTML)
    assert catalog[("brand", "pride")][0] == "پراید"
    assert catalog[("brand", "bmw")][0] == "ب ام و"
    assert catalog[("brand", "toyota")][0] == "تویوتا"
    assert catalog[("model", "pride", "111")][0] == "پراید 111"


def test_bilingual_label_puts_persian_beside_latin():
    assert bilingual_label(fa="پراید", en="PRIDE", slug="pride") == "پراید Pride"
    assert bilingual_label(fa="ب ام و", en="bmw", slug="bmw") == "ب ام و BMW"
    assert bilingual_label(fa="تویوتا", en="toyota", slug="toyota") == "تویوتا Toyota"


def test_apply_review_labels_on_classified_urls():
    classified = classify_taxonomy_urls(
        [
            "https://bama.ir/car/pride",
            "https://bama.ir/car/pride-111",
            "https://bama.ir/car/porsche",
            "https://bama.ir/car/porsche-panamera",
        ]
    )
    labeled = apply_review_labels(classified, {"car": _REVIEWS_HTML})
    by_key = {(item.term_type, item.slug): item.label for item in labeled}
    assert "پراید" in by_key[("brand", "pride")]
    assert "Pride" in by_key[("brand", "pride")]
    assert "پراید" in by_key[("model", "111")]
    assert by_key[("brand", "porsche")] == "porsche"
    assert by_key[("model", "panamera")] == "panamera"


def test_apply_review_labels_merges_brand_review_pages():
    classified = classify_taxonomy_urls(
        [
            "https://bama.ir/car/pride",
            "https://bama.ir/car/pride-141",
        ]
    )
    labeled = apply_review_labels(
        classified,
        {
            "car": [
                '<a href="/car-reviews/pride">pride پراید</a>',
                '<a href="/car-reviews/pride/141-specs-1307-sl">141 پراید</a>',
            ]
        },
    )
    by_key = {(item.term_type, item.slug): item.label for item in labeled}
    assert "پراید" in by_key[("brand", "pride")]
    assert "پراید" in by_key[("model", "141")]
    assert "141" in by_key[("model", "141")]
