from crawler.domain.url_patterns import infer_url_pattern


def test_infer_url_pattern_car_detail():
    pattern = infer_url_pattern("https://bama.ir/car/detail-12345")
    assert "{id}" in pattern
    assert "detail" in pattern


def test_infer_url_pattern_motorcycle():
    pattern = infer_url_pattern("https://bama.ir/motorcycle/yamaha")
    assert "motorcycle" in pattern
