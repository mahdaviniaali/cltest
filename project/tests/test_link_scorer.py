from config.bama_site import load_bama_site_config
from crawler.domain.link_scorer import infer_page_role, match_route_pattern, score_url


def test_motorcycle_root_weight_equals_car_at_same_depth():
    config = load_bama_site_config()
    car = score_url("https://bama.ir/car", config)
    moto = score_url("https://bama.ir/motorcycle", config)
    assert car == moto == 100


def test_section_root_prefix_weight():
    config = load_bama_site_config()
    assert config.section_weight_for_url("https://bama.ir/car/bmw") == 10
    assert config.section_weight_for_url("https://bama.ir/motorcycle/yamaha") == 10


def test_ad_detail_lower_weight_than_section_hub():
    config = load_bama_site_config()
    hub = score_url("https://bama.ir/car", config)
    detail = score_url("https://bama.ir/car/detail-12345", config)
    assert hub > detail


def test_match_route_pattern_detail_template():
    assert match_route_pattern(
        "https://bama.ir/car/detail-99",
        "https://bama.ir/car/detail-{id}",
        "https://bama.ir/car/detail-{id}",
    )


def test_infer_page_role_from_yaml_only():
    config = load_bama_site_config()
    role = infer_page_role("https://bama.ir/car/detail-42", config)
    assert role == "ad_detail"

    slug_role = infer_page_role(
        "https://bama.ir/car/detail-aojbfxng-capra-2-4wd-1400",
        config,
    )
    assert slug_role == "ad_detail"

    hub = infer_page_role("https://bama.ir/motorcycle", config)
    assert hub == "section_hub"


def test_route_rule_priority():
    config = load_bama_site_config()
    rule = config.match_route_rule(
        "https://bama.ir/car/detail-1",
        "https://bama.ir/car/detail-{id}",
    )
    assert rule is not None
    assert rule.role == "ad_detail"
