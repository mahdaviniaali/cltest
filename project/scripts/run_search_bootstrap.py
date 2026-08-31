"""Run bootstrap crawl for a search (sync, for debugging/recovery)."""
import sys
from pathlib import Path
from uuid import uuid4

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))
sys.path.insert(0, str(PROJECT_DIR))

import app.models.advertisement  # noqa: F401
import app.models.crawl_job  # noqa: F401
import app.models.match  # noqa: F401
import app.models.notification  # noqa: F401
import app.models.outbox_event  # noqa: F401
import app.models.search  # noqa: F401
import app.models.site_map  # noqa: F401
import app.models.taxonomy  # noqa: F401
import app.models.user  # noqa: F401

from app.models.crawl_job import CrawlJobType
from app.models.search import Search
from app.repositories.advertisement_repository import AdvertisementRepository
from app.repositories.crawl_job_repository import CrawlJobRepository
from app.db.engine import SessionLocal
from crawler.application.crawl_job_runner import run_search_bootstrap_job
from crawler.application.search_listing_url_builder import build_search_listing_url

search_id = int(sys.argv[1]) if len(sys.argv) > 1 else 7

session = SessionLocal()
try:
    search = session.get(Search, search_id)
    if search is None:
        raise SystemExit(f"Search {search_id} not found")

    url = build_search_listing_url(session, search)
    before = len(
        AdvertisementRepository(session).list_matching_filter(
            brand=search.brand, model=search.model, limit=200
        )
    )
    print(f"Search {search_id}: {search.brand} / {search.model}")
    print(f"Listing URL: {url}")
    print(f"Matching ads before: {before}")

    jobs = CrawlJobRepository(session)
    job = jobs.create(
        job_type=CrawlJobType.ON_DEMAND_SEARCH.value,
        triggered_by=f"script:bootstrap:{search_id}",
        search_id=search_id,
        idempotency_key=f"script-bootstrap:{search_id}:{uuid4()}",
    )
    session.commit()
    print(f"Running job {job.id} ...")
    run_search_bootstrap_job(session, job.id)

    session.refresh(search)
    after = len(
        AdvertisementRepository(session).list_matching_filter(
            brand=search.brand, model=search.model, limit=200
        )
    )
    print(f"Done. pages={job.pages_crawled} ads_new={job.ads_new} matching_after={after}")
finally:
    session.close()
