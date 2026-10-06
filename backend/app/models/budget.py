from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.user import User


class Budget(Base):
    """Serie de presupuesto: un monto mensual que se repite para una categoría
    desde `starts_on` hasta `ends_on` (exclusivo; `None` = indefinido).

    Las excepciones de un mes concreto (monto distinto, mes saltado o
    presupuesto de un solo mes) viven en `BudgetMonth`. Las series de una
    misma categoría nunca se solapan (lo garantiza `services/budget_operations`).
    `category_name` conserva el nombre si la categoría se borra.
    """

    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    category_name: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    starts_on: Mapped[date] = mapped_column(Date, nullable=False)
    ends_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner: Mapped["User"] = relationship()
    category: Mapped["Category | None"] = relationship()
