from crawler.domain.url_identity import compute_page_key, is_asset_url, normalize_url


def test_normalize_url_strips_fragment_and_lowercases_host():
    assert normalize_url("https://Bama.ir/Car?page=1#top") == "https://bama.ir/Car?page=1"


def test_normalize_url_rejects_mailto():
    assert normalize_url("mailto:a@b.com") is None


def test_is_asset_url():
    assert is_asset_url("https://bama.ir/static/app.js") is True
    assert is_asset_url("https://bama.ir/car") is False


def test_page_key_stable():
    url = "https://bama.ir/car/detail-1"
    assert compute_page_key(url) == compute_page_key(url)
