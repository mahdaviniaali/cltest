from __future__ import annotations

from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser


def robots_url_for(page_url: str) -> str:
    parsed = urlparse(page_url)
    return f"{parsed.scheme}://{parsed.netloc}/robots.txt"


def sitemap_url_for(page_url: str) -> str:
    parsed = urlparse(page_url)
    return f"{parsed.scheme}://{parsed.netloc}/sitemap.xml"


def parse_robots_allowed(robots_text: str, *, user_agent: str, url: str) -> bool:
    parser = RobotFileParser()
    parser.parse(robots_text.splitlines())
    return parser.can_fetch(user_agent, url)


def extract_sitemap_directives(robots_text: str) -> list[str]:
    out: list[str] = []
    for line in robots_text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("sitemap:"):
            out.append(stripped.split(":", 1)[1].strip())
    return out
