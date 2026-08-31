from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.repositories.notification_repository import NotificationRepository
from app.schemas.notifications import NotificationOut, UnreadCountOut

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _to_out(row) -> NotificationOut:
    return NotificationOut(
        id=row.id,
        match_id=row.match_id,
        channel=row.channel,
        title=row.title,
        body=row.body,
        payload=row.payload,
        status=row.status,
        read_at=row.read_at.isoformat() if row.read_at else None,
        sent_at=row.sent_at.isoformat() if row.sent_at else None,
        created_at=row.created_at.isoformat(),
    )


@router.get("", response_model=list[NotificationOut])
def list_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[NotificationOut]:
    rows = NotificationRepository(db).list_for_user(
        user.id,
        unread_only=unread_only,
        limit=limit,
    )
    return [_to_out(row) for row in rows if row.channel == "in_app"]


@router.get("/unread-count", response_model=UnreadCountOut)
def unread_count(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> UnreadCountOut:
    count = NotificationRepository(db).unread_count(user.id)
    return UnreadCountOut(count=count)


@router.patch("/{notification_id}/read", response_model=NotificationOut)
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> NotificationOut:
    repo = NotificationRepository(db)
    row = repo.get_for_user(notification_id, user.id)
    if row is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    repo.mark_read(row)
    db.commit()
    return _to_out(row)


@router.post("/read-all", response_model=UnreadCountOut)
def mark_all_read(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> UnreadCountOut:
    repo = NotificationRepository(db)
    repo.mark_all_read(user.id)
    db.commit()
    return UnreadCountOut(count=0)
