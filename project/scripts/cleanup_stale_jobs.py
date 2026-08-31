"""Fail zombie RUNNING/PAUSED jobs and cancel abandoned PENDING crawl jobs."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))
sys.path.insert(0, str(PROJECT_DIR))

import app.models.advertisement  # noqa: F401
import app.models.crawl_job  # noqa: F401
import app.models.search  # noqa: F401
import app.models.user  # noqa: F401

from app.db.engine import engine, recover_interrupted_jobs
from app.repositories.crawl_job_repository import CrawlJobRepository
from sqlalchemy.orm import sessionmaker


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Fail/cancel all in-flight jobs immediately (ignore CRAWL_JOB_STALE_SECONDS)",
    )
    parser.add_argument(
        "--recover-interrupted",
        action="store_true",
        help="Also mark every RUNNING/PAUSED job as failed (server-restart recovery)",
    )
    args = parser.parse_args()

    max_age = 0 if args.force else None
    session = sessionmaker(bind=engine)()
    try:
        repo = CrawlJobRepository(session)
        stale = repo.reconcile_stale_running_jobs(max_age_seconds=max_age)
        abandoned = repo.reconcile_abandoned_pending_jobs(max_age_seconds=max_age)
        session.commit()
    finally:
        session.close()

    if args.recover_interrupted:
        recover_interrupted_jobs()

    print(f"failed stale running: {stale}")
    print(f"cancelled abandoned pending: {abandoned}")
    if stale or abandoned:
        print("done — refresh the browser and retry بروزرسانی داده‌ها")
    else:
        print("no stale jobs found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
