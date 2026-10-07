from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.core.openapi import AUTH_RESPONSES, Tag
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.transaction import CategorySummary, MonthlySummary

router = APIRouter(prefix="/expenses", tags=[Tag.MOVIMIENTOS], responses=AUTH_RESPONSES)


@router.get(
    "/summary",
    response_model=MonthlySummary,
    summary="Resumen mensual de gastos por categoría",
)
def monthly_summary(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    year: Annotated[int, Query(ge=2000, le=2100, description="Año.", examples=[2026])],
    month: Annotated[int, Query(ge=1, le=12, description="Mes (1–12).", examples=[10])],
) -> MonthlySummary:
    """Total gastado en el mes y desglose por categoría en una lista plana
    (cada subcategoría por separado, en positivo). Solo cuenta gastos no
    borrados; no incluye ingresos ni transferencias.

    Lo usa la página de Movimientos. `GET /dashboard/summary` ofrece un
    resumen más completo (ingresos, neto, fijos/variables) con las
    categorías en árbol."""
    range_start = date(year, month, 1)
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    range_end = date(next_year, next_month, 1)

    rows = (
        db.query(Category.id, Category.name, func.sum(-Transaction.amount))
        .join(Category, Transaction.category_id == Category.id)
        .filter(
            Transaction.owner_id == current_user.id,
            Transaction.direction == "expense",
            Transaction.deleted_at.is_(None),
            Transaction.posted_at >= range_start,
            Transaction.posted_at < range_end,
        )
        .group_by(Category.id, Category.name)
        .order_by(Category.name)
        .all()
    )
    by_category = [
        CategorySummary(category_id=cid, category_name=name, total=total)
        for cid, name, total in rows
    ]
    total = sum((c.total for c in by_category), Decimal("0"))
    return MonthlySummary(year=year, month=month, total=total, by_category=by_category)
