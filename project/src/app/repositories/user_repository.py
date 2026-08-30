from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.auth import hash_password


class UserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_email(self, email: str) -> Optional[User]:
        return self._session.scalar(select(User).where(User.email == email.lower()))

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self._session.get(User, user_id)

    def create(self, email: str, password: str, full_name: str | None = None) -> User:
        user = User(
            email=email.lower(),
            password_hash=hash_password(password),
            full_name=full_name,
        )
        self._session.add(user)
        self._session.commit()
        self._session.refresh(user)
        return user
