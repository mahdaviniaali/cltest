from config.bama_site import BamaSiteConfig, RouteRule
from crawler.domain.link_scorer import infer_page_role, score_url


def test_route_rules_assign_roles_without_hardcoded_regex():
    config = BamaSiteConfig(
        route_rules=[
            RouteRule(pattern="https://bama.ir/car", role="section_hub", weight=100, priority=90),
            RouteRule(
                pattern="https://bama.ir/car/detail-{id}",
                role="ad_detail",
                weight=30,
                priority=50,
            ),
        ],
        section_roots=[],
    )
    assert infer_page_role("https://bama.ir/car", config) == "section_hub"
    assert infer_page_role("https://bama.ir/car/detail-555", config) == "ad_detail"
    assert score_url("https://bama.ir/car", config) == 100
