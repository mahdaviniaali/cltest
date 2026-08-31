"""One-shot cleanup for zombie crawl jobs blocking the UI."""
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "src"))
sys.path.insert(0, str(root))

import app.models.user  # noqa: F401
import app.models.search  # noqa: F401
import app.models.advertisement  # noqa: F401
import app.models.crawl_job  # noqa: F401

from sqlalchemy.orm import sessionmaker
from app.db.engine import engine, recover_interrupted_jobs
from app.repositories.crawl_job_repository import CrawlJobRepository

Session = sessionmaker(bind=engine)
session = Session()
repo = CrawlJobRepository(session)

stale = repo.reconcile_stale_running_jobs(max_age_seconds=0)
abandoned = repo.reconcile_abandoned_pending_jobs(max_age_seconds=0)
session.commit()
session.close()

# Also run full interrupted recovery (safe if API is down)
recover_interrupted_jobs()

print(f"failed stale running: {stale}")
print(f"cancelled abandoned pending: {abandoned}")
print("done — refresh the browser and click بروزرسانی داده‌ها")
