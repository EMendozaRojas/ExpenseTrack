from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationRead, UnreadCount

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _get_owned_notification(db: Session, notification_id: int, current_user: User) -> Notification:
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.owner_id == current_user.id)
        .first()
    )
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notificación no encontrada")
    return notification


@router.get("/", response_model=list[NotificationRead])
def list_notifications(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[Notification]:
    return (
        db.query(Notification)
        .filter(Notification.owner_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )


@router.get("/unread-count", response_model=UnreadCount)
def unread_count(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> UnreadCount:
    count = (
        db.query(Notification)
        .filter(Notification.owner_id == current_user.id, Notification.is_read.is_(False))
        .count()
    )
    return UnreadCount(count=count)


@router.post("/{notification_id}/read", response_model=NotificationRead)
def mark_read(
    notification_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Notification:
    notification = _get_owned_notification(db, notification_id, current_user)
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


@router.post("/read-all", status_code=status.HTTP_204_NO_CONTENT)
def mark_all_read(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    db.query(Notification).filter(
        Notification.owner_id == current_user.id, Notification.is_read.is_(False)
    ).update({"is_read": True})
    db.commit()
