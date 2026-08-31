from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from config import settings


def _configure_sqlite(engine: Engine) -> None:
    if engine.dialect.name != "sqlite":
        return

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.close()


def get_engine():
    connect_args = {}
    if settings.DATABASE_URL.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
    _configure_sqlite(engine)
    return engine


engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db() -> None:
    upgrade_schema(engine)


def upgrade_schema(engine_instance=None) -> None:
    from app.db.migrate import upgrade_schema as _upgrade

    _upgrade(engine_instance or engine)


def recover_interrupted_jobs(engine_instance=None) -> None:
    """Mark in-flight crawl jobs as failed after API restart (background threads do not survive)."""
    from datetime import datetime, timezone

    from sqlalchemy import select
    from sqlalchemy.orm import sessionmaker

    from app.models.crawl_job import CrawlJob, CrawlJobStatus
    from app.repositories.crawl_job_repository import CrawlJobRepository

    eng = engine_instance or engine
    Session = sessionmaker(bind=eng)
    session = Session()
    try:
        now = datetime.now(timezone.utc)
        stmt = select(CrawlJob).where(
            CrawlJob.status.in_(
                [CrawlJobStatus.RUNNING.value, CrawlJobStatus.PAUSED.value]
            )
        )
        for job in session.scalars(stmt).all():
            job.status = CrawlJobStatus.FAILED.value
            job.error = "interrupted by server restart"
            job.finished_at = now
        CrawlJobRepository(session).reconcile_abandoned_pending_jobs(max_age_seconds=0)
        session.commit()
    finally:
        session.close()


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
