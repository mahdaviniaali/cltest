from __future__ import annotations

import hashlib
import re
from urllib.parse import urldefrag, urljoin, urlparse, urlunparse

SKIP_SCHEMES = {"mailto", "tel", "javascript", "data", "ftp"}
ASSET_EXT = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".svg",
    ".ico",
    ".pdf",
    ".zip",
    ".rar",
    ".gz",
    ".mp3",
    ".mp4",
    ".avi",
    ".mov",
    ".wmv",
    ".css",
    ".js",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
}

_SITE_KEY_SAFE = re.compile(r"[^a-z0-9.-]+")


def ensure_http_url(url: str) -> str:
    raw = url.strip()
    if not raw:
        raise ValueError("url must be non-empty")
    if "://" not in raw:
        raw = f"https://{raw}"
    normalized = normalize_url(raw)
    if normalized:
        return normalized
    parsed = urlparse(raw)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return raw
    raise ValueError(f"cannot normalize url: {url!r}")


def site_key_from_url(url: str) -> str | None:
    raw = url.strip()
    if not raw:
        return None
    if "://" not in raw:
        raw = f"https://{raw}"
    host = urlparse(raw).hostname
    if not host:
        return None
    host = host.lower().rstrip(".")
    if host.startswith("www."):
        host = host[4:]
    key = _SITE_KEY_SAFE.sub("-", host).strip("-.")
    return key or None


def normalize_url(url: str, base: str | None = None) -> str | None:
    if base:
        url = urljoin(base, url)
    url, _ = urldefrag(url.strip())
    parsed = urlparse(url)
    if not parsed.scheme or parsed.scheme.lower() in SKIP_SCHEMES:
        return None
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    path = parsed.path or "/"
    netloc = parsed.netloc.lower()
    if netloc.endswith(":80") and parsed.scheme == "http":
        netloc = netloc[:-3]
    elif netloc.endswith(":443") and parsed.scheme == "https":
        netloc = netloc[:-4]
    return urlunparse((parsed.scheme.lower(), netloc, path, "", parsed.query, ""))


def _host_key(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if host.startswith("www."):
        return host[4:]
    return host


def same_domain(url: str, seed: str) -> bool:
    return _host_key(url) == _host_key(seed)


def content_hash(text: str | None) -> str | None:
    if text is None:
        return None
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def compute_page_key(normalized_url: str, web_source_id: str = "") -> str:
    raw = f"{web_source_id}|{normalized_url}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def is_asset_url(url: str) -> bool:
    path = urlparse(url).path.lower()
    return any(path.endswith(ext) for ext in ASSET_EXT)
