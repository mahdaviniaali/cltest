import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DELAY: float = float(os.getenv("CRAWLER_DELAY", "1.0"))
TIMEOUT: int = int(os.getenv("CRAWLER_TIMEOUT", "30"))
USER_AGENT: str = os.getenv(
    "CRAWLER_USER_AGENT",
    "BamaCrawlerBot/1.0 (+https://github.com/cltest)",
)
OUTPUT_DIR: Path = BASE_DIR / os.getenv("CRAWLER_OUTPUT_DIR", "data/")
DATA_DIR: Path = BASE_DIR / "data"
_default_db_path = (DATA_DIR / "app.db").as_posix()
DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{_default_db_path}")

JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-production")
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "10080"))
CORS_ORIGINS: list[str] = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]

# Hybrid crawler
BAMA_LISTING_URL: str = os.getenv("BAMA_LISTING_URL", "https://bama.ir/car")
CRAWL_INTERVAL_SECONDS: int = int(os.getenv("CRAWL_INTERVAL_SECONDS", "300"))
CRAWL_MAX_PAGES: int = int(os.getenv("CRAWL_MAX_PAGES", "10"))
CRAWL_DELAY_SECONDS: float = float(os.getenv("CRAWL_DELAY_SECONDS", "1.0"))
CRAWL_STALENESS_SECONDS: int = int(os.getenv("CRAWL_STALENESS_SECONDS", "600"))
CRAWL_ON_DEMAND_CACHE_MIN_COUNT: int = int(os.getenv("CRAWL_ON_DEMAND_CACHE_MIN_COUNT", "5"))

CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
