from crawler.adapters.bama.parsers import BamaDetailParser, BamaListingParser
from tests.fixtures.bama_html import LISTING_PAGE_1


def test_listing_parser_extracts_newest_first():
    parser = BamaListingParser()
    cards = parser.parse(LISTING_PAGE_1, page=1)
    assert [c.bama_id for c in cards] == ["1003-renault-megan", "1002-renault-megan", "1001-renault-megan"]


def test_listing_parser_extracts_embedded_detail_urls():
    html = """
    <html><body>
      <a href="/car/detail-1001-renault-megan">Renault Megane 1001</a>
      <script>{"url":"/car/detail-1002-renault-megan"}</script>
      <script>{"url":"/car/detail-1003-renault-megan"}</script>
    </body></html>
    """
    parser = BamaListingParser()
    cards = parser.parse(html, page=1)
    assert {c.bama_id for c in cards} == {
        "1001-renault-megan",
        "1002-renault-megan",
        "1003-renault-megan",
    }


def test_detail_parser_splits_persian_comma_title():
    parser = BamaDetailParser()
    draft = parser.parse(
        "<html><body><h1>کی ام سی،  K7</h1></body></html>",
        url="https://bama.ir/car/detail-kmc-k7-1402",
        bama_id="kmc-k7-1402",
    )
    assert draft.brand == "کی ام سی"
    assert draft.model == "K7"


def test_detail_parser_extracts_fields():
    parser = BamaDetailParser()
    draft = parser.parse(
        """
        <html><body>
          <h1>Renault Megane 1390</h1>
          <p>1,500,000,000 تومان</p>
          <p>120,000 کیلومتر</p>
        </body></html>
        """,
        url="https://bama.ir/car/detail-1002-x",
        bama_id="1002",
    )
    assert draft.bama_id == "1002"
    assert draft.price == 1_500_000_000
    assert draft.mileage == 120_000
    assert draft.year == 1390
