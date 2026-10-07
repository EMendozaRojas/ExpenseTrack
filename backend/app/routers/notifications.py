from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.core.openapi import AUTH_RESPONSES, Tag, error_responses
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationRead, UnreadCount
from app.services.notifications import check_budget_notifications, create_month_summary

router = APIRouter(prefix="/notifications", tags=[Tag.NOTIFICACIONES], responses=AUTH_RESPONSES)


def _get_owned_notification(db: Session, notification_id: int, current_user: User) -> Notification:
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.owner_id == current_user.id)
        .first()
    )
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notificación no encontrada")
    return notification


@router.get("/", response_model=list[NotificationRead], summary="Listar notificaciones")
def list_notifications(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[Notification]:
    """Todas las notificaciones del usuario, de la más reciente a la más
    antigua. Las genera el sistema (no hay endpoint para crearlas); también
    se envían por email si está configurado."""
    return (
        db.query(Notification)
        .filter(Notification.owner_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )


@router.get("/unread-count", response_model=UnreadCount, summary="Contar las no leídas")
def unread_count(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> UnreadCount:
    """Número de notificaciones sin leer, para el contador del menú. El
    frontend lo consulta cada minuto."""
    count = (
        db.query(Notification)
        .filter(Notification.owner_id == current_user.id, Notification.is_read.is_(False))
        .count()
    )
    return UnreadCount(count=count)


@router.post(
    "/check", status_code=status.HTTP_204_NO_CONTENT, summary="Revisar avisos al entrar a la app"
)
def check_notifications(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Revisión que el frontend hace una vez al entrar a la app (login o
    recarga): crea los avisos de presupuesto del mes en curso que falten
    (80% y 100%) y el resumen de cierre del mes anterior, si no existían. No
    duplica avisos ya creados."""
    check_budget_notifications(db, current_user)
    create_month_summary(db, current_user)


@router.post(
    "/{notification_id}/read",
    response_model=NotificationRead,
    summary="Marcar como leída",
    responses=error_responses(
        404,
        e404=("La notificación no existe o es de otro usuario.", "Notificación no encontrada"),
    ),
)
def mark_read(
    notification_id: Annotated[int, Path(description="Id de la notificación.", examples=[167])],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Notification:
    """Marca una notificación como leída."""
    notification = _get_owned_notification(db, notification_id, current_user)
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


@router.post(
    "/read-all", status_code=status.HTTP_204_NO_CONTENT, summary="Marcar todas como leídas"
)
def mark_all_read(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Marca como leídas todas las notificaciones del usuario."""
    db.query(Notification).filter(
        Notification.owner_id == current_user.id, Notification.is_read.is_(False)
    ).update({"is_read": True})
    db.commit()
