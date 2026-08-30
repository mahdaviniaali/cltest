import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))
sys.path.insert(0, str(PROJECT_DIR))

from app.db.engine import init_db
from config import settings


def main() -> None:
    init_db()
    print(f"Database initialized: {settings.DATABASE_URL}")


if __name__ == "__main__":
    main()
