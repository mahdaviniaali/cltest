from __future__ import annotations

import json
import re
from pathlib import Path

text = Path("data/_car_reviews.html").read_text(encoding="utf-8")
match = re.search(r"window\.__NUXT__\s*=", text)
print("nuxt idx", match.start() if match else None)
# capture after assignment until </script>
if match:
    start = match.end()
    end = text.find("</script>", start)
    blob = text[start:end].strip()
    if blob.endswith(";"):
        blob = blob[:-1]
    Path("data/_nuxt_blob.js").write_text(blob[:500000], encoding="utf-8")
    print("blob len", len(blob))
    print("blob start", blob[:500])
    print("persian chars", sum(1 for c in blob if "\u0600" <= c <= "\u06FF"))
    # find nearby pride
    idx = blob.lower().find("pride")
    print("pride idx", idx)
    if idx >= 0:
        Path("data/_nuxt_pride_slice.txt").write_text(blob[max(0, idx - 250) : idx + 400], encoding="utf-8")
    toyota = blob.lower().find("toyota")
    print("toyota idx", toyota)
    if toyota >= 0:
        Path("data/_nuxt_toyota_slice.txt").write_text(blob[max(0, toyota - 250) : toyota + 400], encoding="utf-8")
    # find quoted Persian strings near brand objects
    fa = re.findall(r'"([^"\\]{1,40})"', blob)
    persian = [s for s in fa if any("\u0600" <= c <= "\u06FF" for c in s)]
    Path("data/_nuxt_persian_strings.txt").write_text("\n".join(persian[:80]), encoding="utf-8")
    print("persian quoted", len(persian))

