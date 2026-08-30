from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config import settings


def get_engine():
    connect_args = {}
    if settings.DATABASE_URL.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(settings.DATABASE_URL, connect_args=connect_args)


engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db() -> None:
    upgrade_schema(engine)


def upgrade_schema(engine_instance=None) -> None:
    from app.db.migrate import upgrade_schema as _upgrade

    _upgrade(engine_instance or engine)


def recover_interrupted_jobs(engine_instance=None) -> None:
    """Mark site-map jobs left RUNNING after API restart as failed."""
    from datetime import datetime, timezone

    from sqlalchemy import select

    from app.models.crawl_job import CrawlJob, CrawlJobStatus, CrawlJobType

    eng = engine_instance or engine
    Session = sessionmaker(bind=eng)
    session = Session()
    try:
        stmt = select(CrawlJob).where(
            CrawlJob.job_type == CrawlJobType.SITE_MAP.value,
            CrawlJob.status.in_(
                [CrawlJobStatus.RUNNING.value, CrawlJobStatus.PAUSED.value]
            ),
        )
        for job in session.scalars(stmt).all():
            job.status = CrawlJobStatus.FAILED.value
            job.error = "interrupted by server restart"
            job.finished_at = datetime.now(timezone.utc)
        session.commit()
    finally:
        session.close()


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
