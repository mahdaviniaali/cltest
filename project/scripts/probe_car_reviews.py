from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path[:0] = ["src", "."]

from config import settings
from crawler.core.http_client import HttpClient

OUT = Path("data/_car_reviews.html")


def main() -> None:
    http = HttpClient(settings.USER_AGENT, timeout=45)
    try:
        response = http.get("https://bama.ir/car-reviews")
    finally:
        http.close()
    if response is None:
        print("FETCH_FAILED")
        return
    text = response.text
    OUT.write_text(text, encoding="utf-8")
    print("len", len(text))
    print("has __NUXT__", "__NUXT__" in text)
    print("has __NEXT_DATA__", "__NEXT_DATA__" in text)
    print("script count", text.count("<script"))
    lower = text.lower()
    for key in ["brandname", "persianname", "persian", "faname", "namefa", "titlefa", "brandtitle", "displayname"]:
        print(key, lower.count(key))
    hrefs = re.findall(r'href="(/car-reviews/[^"]+)"', text)
    print("hrefs", len(hrefs))
    print("sample", hrefs[:20])
    # JSON-looking blobs
    for m in re.finditer(r'<script[^>]*>(\{.*?\})</script>', text, re.S):
        blob = m.group(1)
        if "pride" in blob.lower() or "porsche" in blob.lower():
            print("json blob len", len(blob), "start", blob[:200].replace("\n", " "))
            break


if __name__ == "__main__":
    main()
