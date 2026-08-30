import sys
import time
from pathlib import Path

import requests

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))
sys.path.insert(0, str(PROJECT_DIR))

base = "http://127.0.0.1:8000"
email = "inspector@test.com"
pwd = "testpass123"

requests.post(
    f"{base}/api/auth/register",
    json={"email": email, "password": pwd, "full_name": "Test"},
)
r = requests.post(f"{base}/api/auth/login", json={"email": email, "password": pwd})
r.raise_for_status()
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

for path in ["/api/inspector/jobs", "/api/inspector/site/tree", "/api/inspector/site/sections"]:
    rr = requests.get(base + path, headers=h, timeout=10)
    print(path, rr.status_code)

start = requests.post(
    f"{base}/api/inspector/site-map/start",
    headers=h,
    json={"max_pages": 5, "max_depth": 2},
    timeout=10,
)
print("start", start.status_code, start.text[:400])

for i in range(6):
    time.sleep(5)
    jobs = requests.get(base + "/api/inspector/jobs", headers=h, timeout=10).json()
    job = jobs[0] if jobs else {}
    events = []
    if job.get("job_id"):
        events = requests.get(
            f"{base}/api/inspector/jobs/{job['job_id']}/events",
            headers=h,
            timeout=10,
        ).json()
    print(
        f"t+{(i+1)*5}s",
        "status=", job.get("status"),
        "crawled=", job.get("pages_crawled"),
        "events=", len(events),
    )
