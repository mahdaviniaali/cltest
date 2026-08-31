from __future__ import annotations

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def _sqlite_columns(engine: Engine, table: str) -> set[str]:
    with engine.connect() as conn:
        rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return {row[1] for row in rows}


def _add_sqlite_column(engine: Engine, table: str, column: str, ddl: str) -> None:
    with engine.begin() as conn:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))


def upgrade_schema(engine: Engine) -> None:
    """Create missing tables and add columns introduced after initial deploy."""
    from app.db.base import Base
    from app.models import (  # noqa: F401
        advertisement,
        crawl_job,
        crawler_state,
        match,
        notification,
        outbox_event,
        search,
        site_map,
        taxonomy,
        user,
    )

    Base.metadata.create_all(bind=engine)

    if engine.dialect.name != "sqlite":
        return

    inspector = inspect(engine)
    if inspector.has_table("crawl_jobs"):
        existing = _sqlite_columns(engine, "crawl_jobs")
        if "pages_discovered" not in existing:
            _add_sqlite_column(engine, "crawl_jobs", "pages_discovered", "INTEGER NOT NULL DEFAULT 0")
        if "pages_failed" not in existing:
            _add_sqlite_column(engine, "crawl_jobs", "pages_failed", "INTEGER NOT NULL DEFAULT 0")
        if "current_depth" not in existing:
            _add_sqlite_column(engine, "crawl_jobs", "current_depth", "INTEGER NOT NULL DEFAULT 0")

    if inspector.has_table("searches"):
        existing = _sqlite_columns(engine, "searches")
        if "bootstrapped_at" not in existing:
            _add_sqlite_column(engine, "searches", "bootstrapped_at", "DATETIME")
        if "last_bootstrap_job_id" not in existing:
            _add_sqlite_column(engine, "searches", "last_bootstrap_job_id", "VARCHAR(36)")

    if inspector.has_table("site_map_groups"):
        existing = _sqlite_columns(engine, "site_map_groups")
        if "inbound_link_count" not in existing:
            _add_sqlite_column(engine, "site_map_groups", "inbound_link_count", "INTEGER NOT NULL DEFAULT 0")
