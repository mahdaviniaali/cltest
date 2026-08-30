from __future__ import annotations

import re
from urllib.parse import urlparse

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.I,
)


_DETAIL_SEGMENT = re.compile(r"^detail-(?P<id>\d+)$", re.I)


def infer_url_pattern(url: str) -> str:
    parsed = urlparse(url)
    segments = [s for s in parsed.path.split("/") if s]
    parts: list[str] = []
    for segment in segments:
        if _UUID_RE.match(segment):
            parts.append("{uuid}")
        elif _DETAIL_SEGMENT.match(segment):
            parts.append("detail-{id}")
        elif len(segment) == 4 and segment.isdigit():
            parts.append("{year}")
        elif segment.isdigit():
            parts.append("{id}")
        else:
            parts.append(segment)
    path = "/" + "/".join(parts) if parts else "/"
    return f"{parsed.scheme}://{parsed.netloc}{path}"


def path_depth(url: str) -> int:
    return len([s for s in urlparse(url).path.split("/") if s])
