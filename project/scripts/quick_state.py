import sqlite3
from pathlib import Path

db = Path(__file__).resolve().parent.parent / "data" / "app.db"
c = sqlite3.connect(db)
print("users:", c.execute("select id, email from users").fetchall())
print("search 2:", c.execute("select id, brand, bootstrapped_at from searches where id=2").fetchone())
print("jobs:", c.execute("select id, status, search_id from crawl_jobs order by created_at desc limit 5").fetchall())
