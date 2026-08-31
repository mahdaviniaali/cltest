"""Filter fingerprint thundering herd — one job per fingerprint under load."""

from __future__ import annotations

import pytest

from app.models.search import Search
from app.repositories.crawl_job_repository import CrawlJobRepository
from app.services.filter_crawl_service import FilterCrawlService

pytestmark = pytest.mark.stress


def test_filter_enqueue_herd_single_job(stress_db_session, stress_scale):
    herd_size = min(stress_scale.searches, 50)
    searches: list[Search] = []
    for i in range(herd_size):
        search = Search(
            user_id=1,
            brand="Porsche",
            model="Panamera",
            enabled=True,
            name=f"herd-{i}",
        )
        searches.append(search)
    stress_db_session.add_all(searches)
    stress_db_session.commit()
    for search in searches:
        stress_db_session.refresh(search)

    service = FilterCrawlService(stress_db_session)
    service.prepare_search(searches[0])
    shared_fp = searches[0].filter_fingerprint
    for search in searches[1:]:
        search.filter_fingerprint = shared_fp
    stress_db_session.commit()

    job_ids: set[str] = set()
    for i, search in enumerate(searches):
        result = service.enqueue_for_search(search, triggered_by=f"stress:{i}", force=True)
        if result.job_id:
            job_ids.add(result.job_id)

    assert len(job_ids) == 1

    jobs = CrawlJobRepository(stress_db_session)
    active = jobs.get_active_for_fingerprint(shared_fp)
    assert active is not None
    assert active.id in job_ids


def test_api_create_same_filter_herd(stress_client, stress_db_session, stress_scale, mock_crawl_dispatch):
    """Concurrent POST /searches with identical criteria should not explode jobs."""
    herd_size = 20
    payload = {"brand": "BMW", "model": "X5", "enabled": True}

    from tests.stress.conftest import run_burst

    def create(_: int) -> int:
        return stress_client.post("/api/searches", json=payload).status_code

    codes = run_burst(herd_size, create)
    assert all(code == 201 for code in codes)

    from sqlalchemy import select
    from app.models.crawl_job import CrawlJob, CrawlJobStatus

    active_jobs = list(
        stress_db_session.scalars(
            select(CrawlJob).where(
                CrawlJob.status.in_(
                    [CrawlJobStatus.PENDING.value, CrawlJobStatus.RUNNING.value]
                )
            )
        )
    )
    fingerprints = {
        s.filter_fingerprint
        for s in stress_db_session.scalars(
            select(Search).where(Search.brand == "BMW", Search.model == "X5")
        )
    }
    assert len(fingerprints) == 1
    assert len(active_jobs) <= 1
