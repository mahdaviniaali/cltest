import sqlite3
from pathlib import Path

db = Path(__file__).resolve().parent.parent / "data" / "app.db"
c = sqlite3.connect(db)
print("ads count:", c.execute("select count(*) from advertisements").fetchone()[0])
rows = c.execute(
    "select id, bama_id, brand, model, title from advertisements limit 15"
).fetchall()
for r in rows:
    print(r)
print("searches:", c.execute("select id, brand, model, bootstrapped_at from searches").fetchall())
print("recent jobs:", c.execute(
    "select id, job_type, status, pages_crawled, ads_new, search_id from crawl_jobs order by created_at desc limit 5"
).fetchall())
