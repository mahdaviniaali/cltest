from types import SimpleNamespace
from unittest.mock import MagicMock

from crawler.application.filter_listing_url_builder import (
    build_bama_query_params,
    build_filter_listing_url,
)


def test_build_bama_query_params():
    params = build_bama_query_params(
        min_year=1400,
        max_price=5_000_000_000,
        max_mileage=0,
        location="tehran",
    )
    assert params["sort"] == "1"
    assert params["yearFrom"] == "1400"
    assert params["priceTo"] == "5000000000"
    assert params["mileage"] == "0"
    assert params["city"] == "tehran"


def test_build_filter_listing_url_merges_path_and_query(monkeypatch):
    session = MagicMock()
    search = SimpleNamespace(
        section_key="car",
        brand="Porsche",
        model="Panamera",
        brand_term_id=None,
        model_term_id=None,
        min_year=1400,
        max_price=None,
        max_mileage=50_000,
        location=None,
    )
    monkeypatch.setattr(
        "crawler.application.filter_listing_url_builder.build_search_listing_url",
        lambda _s, _search: "https://bama.ir/car/porsche/panamera",
    )
    result = build_filter_listing_url(session, search)
    assert result.url.startswith("https://bama.ir/car/porsche/panamera?")
    assert "sort=1" in result.url
    assert "yearFrom=1400" in result.url
    assert "mileageTo=50000" in result.url
    assert result.fingerprint.fingerprint
