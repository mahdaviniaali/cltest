import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DELAY: float = float(os.getenv("CRAWLER_DELAY", "1.0"))
TIMEOUT: int = int(os.getenv("CRAWLER_TIMEOUT", "30"))
USER_AGENT: str = os.getenv(
    "CRAWLER_USER_AGENT",
    "CrawlerBot/1.0 (+https://example.com/bot)",
)
OUTPUT_DIR: Path = BASE_DIR / os.getenv("CRAWLER_OUTPUT_DIR", "data/")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
