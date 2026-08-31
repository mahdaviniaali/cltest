from datetime import datetime, timedelta, timezone

from app.models.filter_crawl_state import FilterCrawlState
from app.models.search import Search
from app.services.filter_crawl_service import FilterCrawlService
from crawler.application.on_demand_crawl import OnDemandCrawlService


def test_filter_freshness_skips_enqueue(db_session):
    search = Search(user_id=1, brand="Dena", model="Plus", enabled=True)
    db_session.add(search)
    db_session.commit()
    db_session.refresh(search)

    FilterCrawlService(db_session).prepare_search(search)
    state = db_session.get(FilterCrawlState, search.filter_fingerprint)
    state.last_crawl_at = datetime.now(timezone.utc)
    db_session.commit()

    enqueue = FilterCrawlService(db_session).enqueue_for_search(
        search,
        triggered_by="test",
    )
    assert enqueue.used_cache is True
    assert enqueue.job_id is None


def test_on_demand_cache_sufficient_when_filter_fresh(db_session):
    search = Search(user_id=1, brand="Dena", enabled=True)
    db_session.add(search)
    db_session.commit()
    db_session.refresh(search)

    FilterCrawlService(db_session).prepare_search(search)
    state = db_session.get(FilterCrawlState, search.filter_fingerprint)
    state.last_crawl_at = datetime.now(timezone.utc)
    db_session.commit()
    db_session.refresh(search)

    cache = OnDemandCrawlService(db_session).evaluate_cache_for_search(search)
    assert cache.filter_fresh is True
    assert cache.sufficient is True


def test_on_demand_cache_stale_when_old_crawl(db_session):
    search = Search(user_id=1, brand="Dena", enabled=True)
    db_session.add(search)
    db_session.commit()
    db_session.refresh(search)

    FilterCrawlService(db_session).prepare_search(search)
    state = db_session.get(FilterCrawlState, search.filter_fingerprint)
    state.last_crawl_at = datetime.now(timezone.utc) - timedelta(minutes=10)
    db_session.commit()
    db_session.refresh(search)

    cache = OnDemandCrawlService(db_session).evaluate_cache_for_search(search)
    assert cache.filter_fresh is False
