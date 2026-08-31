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
    from sqlalchemy import inspect as sa_inspect
    from sqlalchemy.orm import sessionmaker

    from app.db.migrate import upgrade_schema as _upgrade
    from app.repositories.advertisement_repository import AdvertisementRepository

    eng = engine_instance or engine
    _upgrade(eng)
    if not sa_inspect(eng).has_table("advertisements"):
        return
    session = sessionmaker(bind=eng)()
    try:
        repaired = AdvertisementRepository(session).repair_labels_from_titles()
        if repaired:
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def recover_interrupted_jobs(engine_instance=None) -> None:
    """Fail orphaned in-flight jobs after this API process died.

    Background threads do not survive uvicorn reload. Celery workers do —
    if a worker answers ping, leave RUNNING/PENDING jobs alone so a code
    reload does not kill a live crawl or cancel queued tasks.
    """
    from datetime import datetime, timezone

    from sqlalchemy import select
    from sqlalchemy.orm import sessionmaker

    from app.models.crawl_job import CrawlJob, CrawlJobStatus
    from app.services.job_dispatch import celery_worker_available

    if celery_worker_available():
        return

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
        session.commit()
    finally:
        session.close()


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
