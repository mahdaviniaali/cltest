from app.domain.filter_fingerprint import compute_filter_fingerprint


def test_same_criteria_same_fingerprint():
    a = compute_filter_fingerprint(brand="Porsche", model="Panamera", section_key="car")
    b = compute_filter_fingerprint(brand="Porsche", model="Panamera", section_key="car")
    assert a.fingerprint == b.fingerprint
    assert a.source_key.startswith("bama:car:filter:")


def test_term_id_canonicalizes_brand_model():
    by_name = compute_filter_fingerprint(brand="Porsche", model="Panamera")
    by_term = compute_filter_fingerprint(
        brand="porsche",
        model="panamera",
        brand_term_id=10,
        model_term_id=20,
    )
    assert by_name.fingerprint != by_term.fingerprint


def test_whitespace_normalized():
    a = compute_filter_fingerprint(brand="  Porsche ", location=" Tehran ")
    b = compute_filter_fingerprint(brand="Porsche", location="Tehran")
    assert a.fingerprint == b.fingerprint
