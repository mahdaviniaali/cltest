import time
import requests

base = "http://127.0.0.1:8000"
r = requests.post(f"{base}/api/auth/register", json={"email": "fix2@test.com", "password": "test1234"})
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}
sr = requests.post(f"{base}/api/searches", json={"brand": "Dena", "enabled": True}, headers=h)
body = sr.json()
print("create", sr.status_code, body.get("is_crawling"), body.get("job_id"))
job_id = body.get("job_id")
search_id = body["id"]
for _ in range(25):
    time.sleep(3)
    j = requests.get(f"{base}/api/crawl/jobs/{job_id}", headers=h)
    if j.status_code == 200:
        data = j.json()
        print("job", data["status"], "pages", data.get("pages_crawled"), "ads_new", data.get("ads_new"))
        if data["status"] in ("completed", "failed"):
            break
res = requests.get(f"{base}/api/searches/{search_id}/results", headers=h)
print("results total_count", res.json().get("total_count"))
