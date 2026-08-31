import sqlite3
from pathlib import Path

db = Path(__file__).resolve().parent.parent / "data" / "app.db"
c = sqlite3.connect(db)
print("=== running/pending jobs ===")
for row in c.execute(
    "select id, job_type, status, search_id, pages_crawled, ads_new, started_at, created_at, error "
    "from crawl_jobs where status in ('running', 'pending') order by created_at"
):
    print(row)
