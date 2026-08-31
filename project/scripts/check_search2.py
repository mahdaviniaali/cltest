import sqlite3
from pathlib import Path

db = Path(__file__).resolve().parent.parent / "data" / "app.db"
c = sqlite3.connect(db)

print("=== search 2 ===")
print(c.execute("select id, brand, bootstrapped_at from searches where id=2").fetchone())

print("\n=== latest jobs for search 2 ===")
for row in c.execute(
    "select id, status, pages_crawled, ads_found, ads_new, started_at, finished_at, error "
    "from crawl_jobs where search_id=2 order by created_at desc limit 3"
):
    print(row)

print("\n=== toyota ads count ===")
print(c.execute("select count(*) from advertisements where brand like '%تویوتا%'").fetchone())

print("\n=== any running now ===")
print(c.execute("select id, status, search_id from crawl_jobs where status in ('running','pending')").fetchall())
