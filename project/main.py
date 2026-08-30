import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import settings
from crawler.core.http_client import HttpClient
from crawler.example_crawler import ExampleCrawler
from crawler.storage.json_storage import JsonStorage
from crawler.utils.logger import setup_logging


def main() -> None:
    setup_logging()

    urls = [
        "https://example.com",
    ]

    client = HttpClient(
        user_agent=settings.USER_AGENT,
        timeout=settings.TIMEOUT,
    )

    try:
        crawler = ExampleCrawler(http_client=client, delay=settings.DELAY)
        results = crawler.crawl(urls)

        storage = JsonStorage(settings.OUTPUT_DIR)
        storage.save(results, filename="crawl")
    finally:
        client.close()


if __name__ == "__main__":
    main()
