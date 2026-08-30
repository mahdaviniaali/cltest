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
    from app.db.base import Base
    from app.models import (  # noqa: F401
        advertisement,
        crawl_job,
        crawler_state,
        match,
        notification,
        outbox_event,
        search,
        user,
    )

    Base.metadata.create_all(bind=engine)


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
