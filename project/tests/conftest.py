import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))
sys.path.insert(0, str(PROJECT_DIR))


@pytest.fixture(autouse=True)
def _skip_api_startup_job_recovery():
    """Lifespan must not fail crawl jobs on the developer's real SQLite file."""
    with patch("app.api.main.recover_interrupted_jobs"):
        yield


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    from app.db.base import Base
    import app.models.advertisement  # noqa: F401
    import app.models.crawl_job  # noqa: F401
    import app.models.crawler_state  # noqa: F401
    import app.models.match  # noqa: F401
    import app.models.notification  # noqa: F401
    import app.models.outbox_event  # noqa: F401
    import app.models.filter_crawl_state  # noqa: F401
    import app.models.search  # noqa: F401
    import app.models.site_map  # noqa: F401
    import app.models.user  # noqa: F401

    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    session = Session()
    try:
        yield session
    finally:
        session.close()
