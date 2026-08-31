from app.models.search import Search
from app.repositories.crawl_job_repository import CrawlJobRepository
from app.services.filter_crawl_service import FilterCrawlService


def test_two_searches_same_fingerprint_reuse_job(db_session):
    s1 = Search(user_id=1, brand="Porsche", model="Panamera", enabled=True)
    s2 = Search(user_id=1, brand="Porsche", model="Panamera", enabled=True)
    db_session.add_all([s1, s2])
    db_session.commit()
    db_session.refresh(s1)
    db_session.refresh(s2)

    service = FilterCrawlService(db_session)
    service.prepare_search(s1)
    s2.filter_fingerprint = s1.filter_fingerprint
    db_session.commit()
    db_session.refresh(s2)

    first = service.enqueue_for_search(s1, triggered_by="test:1", force=True)
    second = service.enqueue_for_search(s2, triggered_by="test:2", force=True)

    assert first.job_id is not None
    assert second.job_id == first.job_id

    jobs = CrawlJobRepository(db_session)
    active = jobs.get_active_for_fingerprint(s1.filter_fingerprint)
    assert active is not None
    assert active.id == first.job_id
