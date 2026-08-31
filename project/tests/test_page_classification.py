from config.bama_site import load_bama_site_config
from crawler.adapters.bama.page_classifier import BamaPageClassifier
from crawler.domain.page_classification import classify_url


def test_listing_role_kept_when_mileage_query_stripped_from_canonical():
    config = load_bama_site_config()
    page_type, section, _ = classify_url("https://bama.ir/car/audi?mileage=0", config)
    assert page_type == "listing"
    assert section == "car"


def test_discovered_detail_classified_as_ad_detail():
    config = load_bama_site_config()
    clf = BamaPageClassifier(config)
    result = clf.classify_url_only("https://bama.ir/car/detail-aojbfxng-capra-2-4wd-1400")
    assert result.page_type == "ad_detail"
    assert result.section == "car"
    assert result.url_pattern == "https://bama.ir/car/detail-{id}"


def test_reclassify_nodes_fixes_legacy_hub(db_session):
    from app.models.site_map import SiteNode, SiteNodeStatus
    from app.repositories.site_node_repository import SiteNodeRepository
    from crawler.domain.url_identity import compute_page_key

    node = SiteNode(
        page_key=compute_page_key("https://bama.ir/car/detail-slug-abc"),
        url="https://bama.ir/car/detail-slug-abc",
        url_pattern="https://bama.ir/car/detail-slug-abc",
        depth=2,
        page_type="hub",
        section=None,
        status=SiteNodeStatus.CRAWLED.value,
    )
    db_session.add(node)
    db_session.commit()

    updated = SiteNodeRepository(db_session).reclassify_nodes(load_bama_site_config())
    db_session.commit()
    db_session.refresh(node)

    assert updated >= 1
    assert node.page_type == "ad_detail"
    assert node.section == "car"
    assert node.url_pattern == "https://bama.ir/car/detail-{id}"
