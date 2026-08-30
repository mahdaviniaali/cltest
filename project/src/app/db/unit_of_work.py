from __future__ import annotations

from sqlalchemy.orm import Session


class UnitOfWork:
    """Coordinates a single DB transaction across repositories."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()

    def flush(self) -> None:
        self.session.flush()

    def __enter__(self) -> UnitOfWork:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
