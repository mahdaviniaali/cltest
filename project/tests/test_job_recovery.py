from datetime import datetime, timezone
from unittest.mock import patch
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.engine import recover_interrupted_jobs
from app.models.crawl_job import CrawlJob, CrawlJobStatus, CrawlJobType
import app.models.crawl_job  # noqa: F401
import app.models.search  # noqa: F401
import app.models.user  # noqa: F401


def _engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


def _add_job(session, *, status: str) -> CrawlJob:
    job = CrawlJob(
        id=str(uuid4()),
        job_type=CrawlJobType.SITE_MAP.value,
        status=status,
        triggered_by="test",
        idempotency_key=str(uuid4()),
        started_at=datetime.now(timezone.utc),
    )
    session.add(job)
    session.commit()
    return job


def test_recover_interrupted_jobs_fails_running_when_no_worker():
    engine = _engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    running = _add_job(session, status=CrawlJobStatus.RUNNING.value)
    pending = _add_job(session, status=CrawlJobStatus.PENDING.value)

    with patch("app.services.job_dispatch.celery_worker_available", return_value=False):
        recover_interrupted_jobs(engine)

    session.expire_all()
    assert session.get(CrawlJob, running.id).status == CrawlJobStatus.FAILED.value
    assert session.get(CrawlJob, running.id).error == "interrupted by server restart"
    assert session.get(CrawlJob, pending.id).status == CrawlJobStatus.PENDING.value
    session.close()


def test_recover_interrupted_jobs_leaves_jobs_when_worker_alive():
    engine = _engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    running = _add_job(session, status=CrawlJobStatus.RUNNING.value)

    with patch("app.services.job_dispatch.celery_worker_available", return_value=True):
        recover_interrupted_jobs(engine)

    session.expire_all()
    assert session.get(CrawlJob, running.id).status == CrawlJobStatus.RUNNING.value
    assert session.get(CrawlJob, running.id).error is None
    session.close()
