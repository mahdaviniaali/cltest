from crawler.domain.crawl_policy import CrawlPolicy, parse_sitemap_locs, url_in_scope


def test_url_in_scope_allows_bama_car():
    policy = CrawlPolicy(allow_domains=["bama.ir"], exclude_patterns=["*/login*"])
    assert url_in_scope("https://bama.ir/car", policy, seed="https://bama.ir/") is True


def test_url_in_scope_rejects_assets():
    policy = CrawlPolicy(allow_domains=["bama.ir"])
    assert url_in_scope("https://bama.ir/app.js", policy, seed="https://bama.ir/") is False


def test_url_in_scope_rejects_external():
    policy = CrawlPolicy(allow_domains=["bama.ir"])
    assert url_in_scope("https://google.com/", policy, seed="https://bama.ir/") is False


def test_parse_sitemap_locs():
    xml = """<?xml version="1.0"?><urlset><url><loc>https://bama.ir/car</loc></url></urlset>"""
    assert parse_sitemap_locs(xml) == ["https://bama.ir/car"]
