import re
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))
sys.path.insert(0, str(PROJECT_DIR))

from crawler.adapters.http_page_fetcher import HttpPageFetcher
from crawler.core.http_client import HttpClient
from config import settings

http = HttpClient(settings.USER_AGENT, timeout=30)
fetcher = HttpPageFetcher(http, user_agent=settings.USER_AGENT, respect_robots=False)

candidates = [
    "https://bama.ir/car/porsche/panamera",
    "https://bama.ir/car/porsche/panamera?mileage=0",
    "https://bama.ir/car/porsche/panamera?sort=1",
    "https://bama.ir/car/porsche/panamera?sort=2",
    "https://bama.ir/car/porsche/panamera?yearFrom=1395",
    "https://bama.ir/car/porsche/panamera?priceTo=5000000000",
]

patterns = [
    r"sort[=\":\s]+(\d+)",
    r"mileage[=\":\s]+(\d+)",
    r"yearFrom[=\":\s]+(\d+)",
    r"priceTo[=\":\s]+(\d+)",
    r"city[=\":\s]+[\"']([^\"']+)",
]

for url in candidates:
    html = fetcher.fetch(url) or ""
    print(f"\n=== {url} len={len(html)} ===")
    for pat in patterns:
        found = set(re.findall(pat, html[:80000], re.I))
        if found:
            print(f"  {pat}: {found}")

http.close()
