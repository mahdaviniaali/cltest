import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List

logger = logging.getLogger(__name__)


class JsonStorage:
    """Save crawl results as JSON files."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save(self, data: List[Any], filename: str = "results") -> Path:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filepath = self.output_dir / f"{filename}_{timestamp}.json"

        with filepath.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info("Saved %d records to %s", len(data), filepath)
        return filepath
