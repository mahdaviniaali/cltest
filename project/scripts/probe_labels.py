from __future__ import annotations

import re
from pathlib import Path

from bs4 import BeautifulSoup

text = Path("data/_car_reviews.html").read_text(encoding="utf-8")
soup = BeautifulSoup(text, "lxml")
rows = []
for a in soup.find_all("a", href=True):
    href = a["href"]
    if not href.startswith("/car-reviews/"):
        continue
    label = a.get_text(" ", strip=True)
    if label:
        rows.append((href, label[:120]))

Path("data/_car_reviews_anchors.txt").write_text(
    "\n".join(f"{h}\t{t}" for h, t in rows[:80]),
    encoding="utf-8",
)
print("anchors_with_text", len(rows))

blob = Path("data/_nuxt_blob.js").read_text(encoding="utf-8") if Path("data/_nuxt_blob.js").exists() else ""
title_pairs = re.findall(r'title:\{en:"([^"]+)",fa:"([^"]+)"\}', blob)
model_pairs = re.findall(r'brand_model_en:"([^"]+)",brand_model_fa:"([^"]+)"', blob)
logo = re.findall(r'logo:"([^"]+)"', blob)
print("title_pairs", len(title_pairs), "model_pairs", len(model_pairs), "logos", len(logo))
Path("data/_nuxt_title_pairs.txt").write_text(
    "\n".join(f"{en}\t{fa}" for en, fa in title_pairs[:40]),
    encoding="utf-8",
)
Path("data/_nuxt_model_pairs.txt").write_text(
    "\n".join(f"{en}\t{fa}" for en, fa in model_pairs[:40]),
    encoding="utf-8",
)
