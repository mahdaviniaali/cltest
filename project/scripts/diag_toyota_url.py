import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "src"))
sys.path.insert(0, str(root))

# Import all models so SQLAlchemy relationships resolve
import app.models.user  # noqa: F401
import app.models.search  # noqa: F401
import app.models.advertisement  # noqa: F401

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import settings
from app.models.search import Search
from crawler.application.search_listing_url_builder import build_search_listing_url
from crawler.adapters.bama.parsers import BamaListingParser
import httpx

engine = create_engine(settings.DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

for sid in (2, 5):
    search = session.get(Search, sid)
    if not search:
        continue
    url = build_search_listing_url(session, search)
    print(f"search {sid} brand={search.brand!r} -> {url}")
    try:
        r = httpx.get(url, headers={"User-Agent": settings.USER_AGENT}, follow_redirects=True, timeout=30)
        print(f"  status={r.status_code} final={r.url} len={len(r.text)}")
        cards = BamaListingParser(str(r.url)).parse(r.text, page=1)
        print(f"  cards={len(cards)}")
    except Exception as e:
        print(f"  ERROR: {e}")

session.close()
