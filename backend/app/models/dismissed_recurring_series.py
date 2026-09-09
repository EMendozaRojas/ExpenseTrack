from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DismissedRecurringSeries(Base):
    """Decisión del usuario de descartar una serie recurrente detectada.

    La serie en sí no se persiste (se recalcula bajo demanda); solo se
    guarda que el usuario ya la descartó, para no volver a mostrarla.
    """

    __tablename__ = "dismissed_recurring_series"
    __table_args__ = (
        UniqueConstraint("owner_id", "series_key", name="ux_dismissed_recurring_owner_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    series_key: Mapped[str] = mapped_column(String(300), nullable=False)
    dismissed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
