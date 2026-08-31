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


def _migrate_notifications_v2(engine: Engine) -> None:
    """Recreate notifications with multi-channel unique constraint and inbox fields."""
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS notifications_v2 (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    match_id INTEGER NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    channel VARCHAR(32) NOT NULL DEFAULT 'in_app',
                    title VARCHAR(256),
                    body TEXT,
                    payload JSON,
                    status VARCHAR(16) NOT NULL DEFAULT 'pending',
                    read_at DATETIME,
                    sent_at DATETIME,
                    error TEXT,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(match_id, channel)
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO notifications_v2 (
                    id, match_id, user_id, channel, status, sent_at, error, created_at
                )
                SELECT id, match_id, user_id, channel, status, sent_at, error, created_at
                FROM notifications
                """
            )
        )
        conn.execute(text("DROP TABLE notifications"))
        conn.execute(text("ALTER TABLE notifications_v2 RENAME TO notifications"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_notifications_user_read ON notifications (user_id, read_at)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_notifications_user_created ON notifications (user_id, created_at)"))


def upgrade_schema(engine: Engine) -> None:
    """Create missing tables and add columns introduced after initial deploy."""
    from app.db.base import Base
    from app.models import (  # noqa: F401
        advertisement,
        crawl_job,
        crawler_state,
        filter_crawl_state,
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
        if "section_key" not in existing:
            _add_sqlite_column(engine, "searches", "section_key", "VARCHAR(64) NOT NULL DEFAULT 'car'")
        if "brand_term_id" not in existing:
            _add_sqlite_column(engine, "searches", "brand_term_id", "INTEGER")
        if "model_term_id" not in existing:
            _add_sqlite_column(engine, "searches", "model_term_id", "INTEGER")

    if inspector.has_table("site_map_groups"):
        existing = _sqlite_columns(engine, "site_map_groups")
        if "inbound_link_count" not in existing:
            _add_sqlite_column(engine, "site_map_groups", "inbound_link_count", "INTEGER NOT NULL DEFAULT 0")

    if inspector.has_table("users"):
        existing = _sqlite_columns(engine, "users")
        if "phone" not in existing:
            _add_sqlite_column(engine, "users", "phone", "VARCHAR(32)")
        if "telegram_chat_id" not in existing:
            _add_sqlite_column(engine, "users", "telegram_chat_id", "VARCHAR(64)")
        if "notification_channels" not in existing:
            _add_sqlite_column(
                engine,
                "users",
                "notification_channels",
                "JSON NOT NULL DEFAULT '[\"in_app\"]'",
            )

    if inspector.has_table("notifications"):
        existing = _sqlite_columns(engine, "notifications")
        if "title" not in existing:
            _migrate_notifications_v2(engine)

    if inspector.has_table("crawl_jobs"):
        existing = _sqlite_columns(engine, "crawl_jobs")
        if "filter_fingerprint" not in existing:
            _add_sqlite_column(engine, "crawl_jobs", "filter_fingerprint", "VARCHAR(64)")

    if inspector.has_table("searches"):
        existing = _sqlite_columns(engine, "searches")
        if "filter_fingerprint" not in existing:
            _add_sqlite_column(engine, "searches", "filter_fingerprint", "VARCHAR(64)")
