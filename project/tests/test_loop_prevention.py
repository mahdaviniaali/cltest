from crawler.domain.url_identity import canonicalize_url, compute_page_key


def test_canonical_dup_same_page_key():
    a = canonicalize_url("https://bama.ir/car?mileage=0", ["mileage"]) or ""
    b = canonicalize_url("https://bama.ir/car?mileage=1", ["mileage"]) or ""
    assert compute_page_key(a) == compute_page_key(b)


def test_canonicalize_strips_configured_params():
    url = "https://bama.ir/car?mileage=0&sort=date&brand=bmw"
    canonical = canonicalize_url(url, ["mileage", "sort"])
    assert canonical == "https://bama.ir/car?brand=bmw"
