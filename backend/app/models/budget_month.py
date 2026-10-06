from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.category import Category

BUDGET_MONTH_KINDS = ("single", "override", "skip")


class BudgetMonth(Base):
    """Presupuesto explícito de un mes concreto para una categoría.

    - `single`: presupuesto de un solo mes (no se repite).
    - `override`: monto distinto para un mes cubierto por una serie.
    - `skip`: la serie no aplica ese mes.

    Si existe, gana sobre la serie al resolver el presupuesto del mes.
    `frozen_spent` solo se rellena al borrar la categoría, para conservar lo
    gastado en meses pasados (sus movimientos pasan a "Sin Clasificar").
    """

    __tablename__ = "budget_months"
    __table_args__ = (
        UniqueConstraint(
            "owner_id", "category_id", "month", name="ux_budget_months_owner_category_month"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    category_name: Mapped[str] = mapped_column(String(100), nullable=False)
    month: Mapped[date] = mapped_column(Date, nullable=False)
    kind: Mapped[str] = mapped_column(String(10), nullable=False)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    frozen_spent: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    category: Mapped["Category | None"] = relationship()
