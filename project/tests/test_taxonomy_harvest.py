from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.repositories.taxonomy_repository import TaxonomyRepository
from config.bama_site import load_bama_site_config
from crawler.application.taxonomy_harvest import TaxonomyHarvestService


class FakeRawFetcher:
    def __init__(self, pages: dict[str, str | None]) -> None:
        self.pages = pages
        self.calls: list[str] = []

    def fetch_raw(self, url: str) -> str | None:
        self.calls.append(url)
        return self.pages.get(url)


def _db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    import app.models.advertisement  # noqa: F401
    import app.models.crawl_job  # noqa: F401
    import app.models.crawler_state  # noqa: F401
    import app.models.match  # noqa: F401
    import app.models.notification  # noqa: F401
    import app.models.outbox_event  # noqa: F401
    import app.models.search  # noqa: F401
    import app.models.site_map  # noqa: F401
    import app.models.taxonomy  # noqa: F401
    import app.models.user  # noqa: F401

    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session


def _sitemap_xml(*locs: str) -> str:
    body = "".join(f"<url><loc>{loc}</loc></url>" for loc in locs)
    return f'<?xml version="1.0"?><urlset>{body}</urlset>'


def test_taxonomy_harvest_from_sitemaps():
    session = _db_session()
    try:
        robots = "User-agent: *\nSitemap: https://bama.ir/sitemap/car\n"
        car_xml = _sitemap_xml(
            "https://bama.ir/car/porsche",
            "https://bama.ir/car/porsche-panamera",
            "https://bama.ir/car/pride",
            "https://bama.ir/car/pride-111",
            "https://bama.ir/car/all/tehran-tehran",
        )
        fetcher = FakeRawFetcher(
            {
                "https://bama.ir/robots.txt": robots,
                "https://bama.ir/sitemap/car": car_xml,
                "https://bama.ir/sitemap/motorcycle": _sitemap_xml("https://bama.ir/motorcycle/honda"),
                "https://bama.ir/sitemap/truck": None,
                "https://bama.ir/car-reviews": (
                    '<a href="/car-reviews/pride">pride پراید</a>'
                    '<a href="/car-reviews/pride/111-specs-1">pride 111 پراید 111</a>'
                    '<script>title:{en:"PRIDE",fa:"پراید"}'
                    'brand_model_en:"pride 111",brand_model_fa:"پراید 111"</script>'
                ),
            }
        )
        summary = TaxonomyHarvestService(
            session,
            config=load_bama_site_config(),
            fetcher=fetcher,
        ).harvest(job_id="harvest-1")
        session.commit()

        assert summary["brands"] >= 3
        assert summary["models"] >= 2
        repo = TaxonomyRepository(session)
        car_brands = {t.slug for t in repo.list_terms(section_key="car", term_type="brand")}
        assert car_brands == {"porsche", "pride"}
        models = repo.list_terms(section_key="car", term_type="model")
        assert {m.slug for m in models} == {"panamera", "111"}
        pride = next(t for t in repo.list_terms(section_key="car", term_type="brand") if t.slug == "pride")
        assert "پراید" in pride.label
        pride_111 = next(t for t in models if t.slug == "111")
        assert "پراید" in pride_111.label
        porsche = next(t for t in repo.list_terms(section_key="car", term_type="brand") if t.slug == "porsche")
        assert porsche.label == "porsche"
        moto = repo.list_terms(section_key="motorcycle", term_type="brand")
        assert [t.slug for t in moto] == ["honda"]
    finally:
        session.close()
