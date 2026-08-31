from bs4 import BeautifulSoup
import re
from config import settings
from crawler.adapters.http_page_fetcher import HttpPageFetcher
from crawler.core.http_client import HttpClient

http = HttpClient(settings.USER_AGENT, timeout=30)
fetcher = HttpPageFetcher(http, user_agent=settings.USER_AGENT, respect_robots=False)
html = fetcher.fetch("https://bama.ir/car") or ""
soup = BeautifulSoup(html, "lxml")
hrefs = [a.get("href", "") for a in soup.find_all("a", href=True)]
detail_hrefs = [h for h in hrefs if "detail" in h.lower()]
print("anchor detail hrefs", len(detail_hrefs))
print("samples", detail_hrefs[:8])
slug_re = re.compile(r"/car/detail-[a-z0-9-]+", re.I)
json_urls = slug_re.findall(html)
print("slug urls in html", len(json_urls), json_urls[:5])
http.close()
