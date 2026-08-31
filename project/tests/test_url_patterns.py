from crawler.domain.url_patterns import infer_url_pattern


def test_infer_url_pattern_car_detail():
    pattern = infer_url_pattern("https://bama.ir/car/detail-12345")
    assert pattern == "https://bama.ir/car/detail-{id}"


def test_infer_url_pattern_car_detail_slug():
    pattern = infer_url_pattern("https://bama.ir/car/detail-aojbfxng-capra-2-4wd-1400")
    assert pattern == "https://bama.ir/car/detail-{id}"


def test_infer_url_pattern_motorcycle():
    pattern = infer_url_pattern("https://bama.ir/motorcycle/yamaha")
    assert "motorcycle" in pattern
