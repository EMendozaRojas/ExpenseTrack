from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.user import User


class Budget(Base):
    """Tope mensual de gasto para una categoría (raíz o subcategoría).

    Recurrente: un mismo `Budget` se evalúa contra cualquier mes que se
    consulte (no hay una fila por mes). Sin rollover ni alertas persistidas
    en esta primera versión — el estado se calcula al vuelo en el GET.
    """

    __tablename__ = "budgets"
    __table_args__ = (UniqueConstraint("owner_id", "category_id", name="ux_budgets_owner_category"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner: Mapped["User"] = relationship()
    category: Mapped["Category"] = relationship()
