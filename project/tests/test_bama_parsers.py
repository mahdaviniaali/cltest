from crawler.adapters.bama.parsers import BamaDetailParser, BamaListingParser
from tests.fixtures.bama_html import LISTING_PAGE_1


def test_listing_parser_extracts_newest_first():
    parser = BamaListingParser()
    cards = parser.parse(LISTING_PAGE_1, page=1)
    assert [c.bama_id for c in cards] == ["1003", "1002", "1001"]


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
