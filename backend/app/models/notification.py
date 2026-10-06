from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

NOTIFICATION_TYPES = (
    "budget_warning",
    "budget_exceeded",
    "budget_month_summary",
    "budget_category_deleted",
    "goal_near",
    "goal_reached",
)


class Notification(Base):
    """Notificación generada por el sistema (presupuestos/metas), mostrada en
    la pestaña Notificaciones y enviada por correo. `period_key` + `related_id`
    + `type` evita duplicados: un presupuesto no reavisa dos veces el mismo
    mes, una meta no reavisa dos veces el mismo umbral."""

    __tablename__ = "notifications"
    __table_args__ = (
        UniqueConstraint(
            "owner_id", "type", "related_id", "period_key", name="ux_notifications_dedupe"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(String(500), nullable=False)
    related_id: Mapped[int] = mapped_column(Integer, nullable=False)
    period_key: Mapped[str] = mapped_column(String(10), nullable=False, default="")
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
