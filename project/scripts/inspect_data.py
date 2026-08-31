"""Inspect crawled data quality — run: python scripts/inspect_data.py [--reclassify]"""
from __future__ import annotations

import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "data" / "app.db"
PROJECT = Path(__file__).resolve().parent.parent


def _maybe_reclassify_nodes() -> None:
    if "--reclassify" not in sys.argv and "--reclassify-discovered" not in sys.argv:
        return
    sys.path.insert(0, str(PROJECT / "src"))
    sys.path.insert(0, str(PROJECT))
    import app.models.site_map  # noqa: F401
    from app.db.engine import SessionLocal
    from app.repositories.site_node_repository import SiteNodeRepository
    from config.bama_site import load_bama_site_config
    from crawler.application.site_catalog_builder import SiteCatalogBuilder
    from crawler.application.site_map_projection_builder import SiteMapProjectionBuilder

    config = load_bama_site_config()
    session = SessionLocal()
    try:
        repo = SiteNodeRepository(session)
        if "--reclassify-discovered" in sys.argv and "--reclassify" not in sys.argv:
            n = repo.reclassify_discovered(config)
        else:
            n = repo.reclassify_nodes(config)
        sections = SiteCatalogBuilder(session, config).build()
        map_groups = SiteMapProjectionBuilder(session, config).build()
        session.commit()
        print(f"Reclassified {n} site nodes")
        print(f"Rebuilt {len(sections)} site sections")
        print(f"Rebuilt {len(map_groups)} site map groups\n")
    finally:
        session.close()


def main() -> None:
    _maybe_reclassify_nodes()
    if not DB.exists():
        print("NO DB at", DB)
        return

    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row

    print("=== COUNTS ===")
    sys.path.insert(0, str(PROJECT / "src"))
    sys.path.insert(0, str(PROJECT))
    from app.db.engine import SessionLocal
    from app.services.stats_service import StatsService

    session = SessionLocal()
    try:
        for row in StatsService(session).table_counts():
            print(f"  {row.table}: {row.count}")
    finally:
        session.close()

    print("\n=== SITE SECTIONS ===")
    rows = c.execute(
        "SELECT section_key, label, page_count, useful_score, root_urls, url_patterns "
        "FROM site_sections ORDER BY useful_score DESC"
    ).fetchall()
    if not rows:
        print("  (empty — catalog not built or single-section fallback)")
    for r in rows:
        pats = json.loads(r["url_patterns"] or "[]")
        roots = json.loads(r["root_urls"] or "[]")
        print(f"  [{r['section_key']}] {r['label']} — pages={r['page_count']} score={r['useful_score']}")
        print(f"    roots: {roots[:3]}")
        print(f"    top patterns: {pats[:5]}")

    print("\n=== PAGE TYPE × SECTION ===")
    for r in c.execute(
        "SELECT page_type, COALESCE(section,'(none)') sec, COUNT(*) n "
        "FROM site_nodes GROUP BY page_type, section ORDER BY n DESC LIMIT 20"
    ):
        print(f"  {r['page_type']:10} {r['sec']:15} {r['n']}")

    print("\n=== URL PATTERN TOP 15 ===")
    for r in c.execute(
        "SELECT url_pattern, page_type, COUNT(*) n FROM site_nodes "
        "GROUP BY url_pattern, page_type ORDER BY n DESC LIMIT 15"
    ):
        print(f"  n={r['n']:4} type={r['page_type']:8} {r['url_pattern']}")

    print("\n=== SAMPLE AD DETAIL PAGES (page_role=ad_detail) ===")
    for r in c.execute(
        "SELECT url, title, section, url_pattern, excerpt FROM site_nodes "
        "WHERE page_type IN ('detail','ad_detail') LIMIT 8"
    ):
        print(f"  URL: {r['url']}")
        print(f"    title: {(r['title'] or '')[:80]}")
        print(f"    section: {r['section']} pattern: {r['url_pattern']}")
        print()

    print("=== SAMPLE LISTING/HUB PAGES ===")
    for r in c.execute(
        "SELECT url, title, page_type, section FROM site_nodes "
        "WHERE page_type IN ('listing','hub','section_hub','model_hub') LIMIT 8"
    ):
        print(f"  [{r['page_type']}] {r['url']}")
        print(f"    title: {(r['title'] or '')[:80]} section={r['section']}")
        print()

    print("=== CLASSIFICATION ISSUES (unknown/static on car paths) ===")
    bad = c.execute(
        "SELECT COUNT(*) FROM site_nodes WHERE page_type IN ('unknown','static') "
        "AND url LIKE '%bama.ir/car%'"
    ).fetchone()[0]
    total_car = c.execute(
        "SELECT COUNT(*) FROM site_nodes WHERE url LIKE '%bama.ir/car%'"
    ).fetchone()[0]
    print(f"  car URLs: {total_car}, unknown/static: {bad}")

    print("\n=== TITLES LOOKING WRONG (very short or generic) ===")
    for r in c.execute(
        "SELECT url, title, page_type FROM site_nodes "
        "WHERE length(COALESCE(title,'')) < 5 OR title IS NULL LIMIT 10"
    ):
        print(f"  {r['page_type']:8} {(r['title'] or '(null)'):20} {r['url'][:70]}")

    print("\n=== ADVERTISEMENTS (incremental crawl) ===")
    ad_count = c.execute("SELECT COUNT(*) FROM advertisements").fetchone()[0]
    print(f"  total ads: {ad_count}")
    for r in c.execute(
        "SELECT bama_id, title, brand, year, price, url FROM advertisements "
        "ORDER BY crawled_at DESC LIMIT 5"
    ):
        print(f"  {dict(r)}")

    print("\n=== SEARCHES ===")
    for r in c.execute(
        "SELECT id, brand, model, bootstrapped_at, enabled FROM searches ORDER BY id"
    ):
        print(
            f"  id={r['id']} brand={r['brand']!r} model={r['model']!r} "
            f"bootstrapped={r['bootstrapped_at']} enabled={r['enabled']}"
        )

    print("\n=== IN-FLIGHT CRAWL JOBS (running/pending) ===")
    inflight = c.execute(
        "SELECT id, job_type, status, search_id, pages_crawled, ads_new, "
        "datetime(started_at), datetime(created_at), error "
        "FROM crawl_jobs WHERE status IN ('running', 'pending') ORDER BY created_at"
    ).fetchall()
    if not inflight:
        print("  (none)")
    for r in inflight:
        print(
            f"  {r['id'][:8]}… {r['job_type']:18} {r['status']:8} "
            f"search={r['search_id']} pages={r['pages_crawled']} ads_new={r['ads_new']}"
        )
        if r["error"]:
            print(f"    error: {r['error']}")

    print("\n=== RECENT CRAWL JOBS ===")
    for r in c.execute(
        "SELECT id, job_type, status, search_id, pages_crawled, ads_found, ads_new, "
        "datetime(started_at), datetime(finished_at), error FROM crawl_jobs "
        "ORDER BY created_at DESC LIMIT 8"
    ):
        print(
            f"  {r['id'][:8]}… {r['job_type']:18} {r['status']:10} "
            f"search={r['search_id']} crawled={r['pages_crawled']} "
            f"ads={r['ads_found']}/{r['ads_new']}"
        )
        if r["error"]:
            print(f"    error: {r['error']}")

    # Edge stats
    print("\n=== GRAPH ===")
    print(f"  edges: {c.execute('SELECT COUNT(*) FROM site_edges').fetchone()[0]}")
    avg_links = c.execute(
        "SELECT AVG(json_extract(meta,'$.link_count')) FROM site_nodes WHERE meta IS NOT NULL"
    ).fetchone()[0]
    print(f"  avg links/page: {avg_links:.1f}" if avg_links else "  avg links/page: n/a")

    statuses = Counter(
        r[0]
        for r in c.execute("SELECT status FROM site_nodes").fetchall()
    )
    print(f"  node statuses: {dict(statuses)}")

    print("\n=== DETAIL URL CHECK ===")
    detail_urls = c.execute(
        "SELECT COUNT(*) FROM site_nodes WHERE url LIKE '%detail-%'"
    ).fetchone()[0]
    print(f"  nodes with detail- in URL: {detail_urls}")

    print("\n=== DUPLICATE PATTERNS ===")
    for r in c.execute(
        "SELECT url_pattern, COUNT(*) n FROM site_nodes "
        "GROUP BY url_pattern HAVING n > 1 ORDER BY n DESC LIMIT 8"
    ):
        print(f"  n={r['n']} {r['url_pattern']}")

    print("\n=== DEPTH DISTRIBUTION ===")
    for r in c.execute("SELECT depth, COUNT(*) n FROM site_nodes GROUP BY depth ORDER BY depth"):
        print(f"  depth {r['depth']}: {r['n']}")

    print("\n=== OTHER SECTIONS (motorcycle/truck/news) ===")
    for sec in ("motorcycle", "truck", "news"):
        n = c.execute(
            "SELECT COUNT(*) FROM site_nodes WHERE section=? OR url LIKE ?",
            (sec, f"%/{sec}%"),
        ).fetchone()[0]
        print(f"  {sec}: {n}")

    print("\n=== EXAMPLE BRAND TAXONOMY (hub pages) ===")
    for r in c.execute(
        "SELECT url, title FROM site_nodes WHERE page_type IN ('hub','section_hub','model_hub') "
        "AND url LIKE '%/car/%' "
        "AND url NOT LIKE '%?%' ORDER BY url LIMIT 12"
    ):
        print(f"  {r['url']}")
        print(f"    → {(r['title'] or '')[:70]}")


if __name__ == "__main__":
    main()
