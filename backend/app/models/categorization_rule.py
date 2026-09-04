from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.user import User

MATCH_TYPES = ("contains", "starts_with")


class CategorizationRule(Base):
    """Regla que asigna una categoría a un movimiento según su descripción normalizada.

    owner_id nulo = regla del sistema, aplica a todos los usuarios con menor prioridad
    que cualquier regla propia del usuario.
    """

    __tablename__ = "categorization_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    match_type: Mapped[str] = mapped_column(String(20), nullable=False, default="contains")
    pattern: Mapped[str] = mapped_column(String(255), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner: Mapped["User | None"] = relationship()
    category: Mapped["Category"] = relationship(back_populates="rules")
