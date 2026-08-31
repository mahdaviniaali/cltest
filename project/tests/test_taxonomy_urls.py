from crawler.domain.taxonomy_urls import classify_taxonomy_urls


def test_classify_nested_and_hyphenated_models():
    classified = classify_taxonomy_urls(
        [
            "https://bama.ir/car/porsche",
            "https://bama.ir/car/porsche/panamera",
            "https://bama.ir/car/porsche-panamera",
            "https://bama.ir/car/porsche-panamera?mileage=0",
            "https://bama.ir/car/pride",
            "https://bama.ir/car/pride-111",
            "https://bama.ir/car/pride-111-ex",
            "https://bama.ir/car/all/tehran-tehran",
            "https://bama.ir/car/detail-abc-porsche-panamera",
            "https://bama.ir/truck/akia/azarbaijan_sharghi-bostan_abad",
        ]
    )
    brands = {item.slug: item for item in classified if item.term_type == "brand" and item.section == "car"}
    models = {
        (item.brand_slug, item.slug): item
        for item in classified
        if item.term_type == "model" and item.section == "car"
    }

    assert "porsche" in brands
    assert "pride" in brands
    assert "all" not in brands
    assert "pride-111" not in brands

    assert ("porsche", "panamera") in models
    assert models[("porsche", "panamera")].listing_url in {
        "https://bama.ir/car/porsche/panamera",
        "https://bama.ir/car/porsche-panamera",
    }
    assert ("pride", "111") in models
    assert ("pride", "111-ex") in models
    assert models[("pride", "111")].listing_url == "https://bama.ir/car/pride-111"
    assert all(item.listing_url != "https://bama.ir/truck/akia/azarbaijan_sharghi-bostan_abad" for item in classified)


def test_classify_motorcycle_brands():
    classified = classify_taxonomy_urls(
        [
            "https://bama.ir/motorcycle/honda",
            "https://bama.ir/motorcycle/honda-cb1300",
        ]
    )
    brands = [item.slug for item in classified if item.term_type == "brand"]
    models = [item.slug for item in classified if item.term_type == "model"]
    assert brands == ["honda"]
    assert models == ["cb1300"]
