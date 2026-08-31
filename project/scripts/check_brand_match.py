import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "src"))
sys.path.insert(0, str(root))

import app.models.user  # noqa: F401
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import settings
from app.repositories.advertisement_repository import AdvertisementRepository

engine = create_engine(settings.DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()
repo = AdvertisementRepository(session)

for brand in ("Dena", "دنا", "تویوتا", "Toyota"):
    ads = repo.list_matching_filter(brand=brand, limit=5)
    print(f"brand={brand!r} -> {len(ads)} ads")

session.close()
