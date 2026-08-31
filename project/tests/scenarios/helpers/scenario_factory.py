from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.advertisement import Advertisement
from app.models.filter_crawl_state import FilterCrawlState
from app.models.search import Search
from app.models.user import User
from app.services.auth import hash_password
from app.services.filter_crawl_service import FilterCrawlService
from crawler.adapters.db_ad_store import DbAdStore
from crawler.domain.entities import AdDraft


class UserFactory:
  @staticmethod
  def create(
      session: Session,
      *,
      email: str,
      password: str = "secret123",
      full_name: Optional[str] = None,
  ) -> User:
      user = User(
          email=email,
          password_hash=hash_password(password),
          full_name=full_name,
          notification_channels=["in_app", "log"],
      )
      session.add(user)
      session.commit()
      session.refresh(user)
      return user


class AdFactory:
  @staticmethod
  def seed_matching_ads(
      session: Session,
      *,
      brand: str,
      model: Optional[str] = None,
      count: int = 5,
      prefix: str = "ad",
      **overrides: Any,
  ) -> list[Advertisement]:
      now = datetime.now(timezone.utc)
      ads: list[Advertisement] = []
      for i in range(count):
          ad = Advertisement(
              bama_id=f"{prefix}-{brand}-{i}",
              url=f"https://bama.ir/car/detail-{prefix}-{i}",
              title=f"{brand} {model or ''} {i}".strip(),
              brand=brand,
              model=model,
              crawled_at=now,
              **overrides,
          )
          session.add(ad)
          ads.append(ad)
      session.commit()
      for ad in ads:
          session.refresh(ad)
      return ads

  @staticmethod
  def discover_new(
      session: Session,
      *,
      bama_id: str,
      brand: Optional[str] = None,
      model: Optional[str] = None,
      year: Optional[int] = None,
      price: Optional[int] = None,
      mileage: Optional[int] = None,
      location: Optional[str] = None,
      title: Optional[str] = None,
  ) -> tuple[Advertisement, bool]:
      draft = AdDraft(
          bama_id=bama_id,
          url=f"https://bama.ir/car/detail-{bama_id}",
          title=title or f"{brand or 'Car'} {model or ''}".strip(),
          brand=brand,
          model=model,
          year=year,
          price=price,
          mileage=mileage,
          location=location,
      )
      ad_id, created = DbAdStore(session).save_new(draft)
      ad = session.get(Advertisement, ad_id)
      assert ad is not None
      return ad, created


class FilterFactory:
  @staticmethod
  def create_search(
      session: Session,
      user_id: int,
      *,
      brand: Optional[str] = None,
      model: Optional[str] = None,
      min_year: Optional[int] = None,
      max_price: Optional[int] = None,
      max_mileage: Optional[int] = None,
      location: Optional[str] = None,
      enabled: bool = True,
      name: Optional[str] = None,
  ) -> Search:
      search = Search(
          user_id=user_id,
          name=name,
          brand=brand,
          model=model,
          min_year=min_year,
          max_price=max_price,
          max_mileage=max_mileage,
          location=location,
          enabled=enabled,
      )
      session.add(search)
      session.commit()
      session.refresh(search)
      FilterCrawlService(session).prepare_search(search)
      session.commit()
      session.refresh(search)
      return search

  @staticmethod
  def mark_fresh(session: Session, search: Search) -> FilterCrawlState:
      state = session.get(FilterCrawlState, search.filter_fingerprint)
      if state is None:
          FilterCrawlService(session).prepare_search(search)
          state = session.get(FilterCrawlState, search.filter_fingerprint)
      assert state is not None
      state.last_crawl_at = datetime.now(timezone.utc)
      session.commit()
      session.refresh(state)
      return state
