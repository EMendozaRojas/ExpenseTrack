from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session, aliased

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.account import Account
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.dashboard import DashboardCategoryNode, DashboardSummary
from app.schemas.transaction import CategorySummary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Umbral de "datos incompletos" (regla de negocio confirmada en producto):
# si el último movimiento del mes en curso es más antiguo que esto, se avisa
# en vez de mostrar un saldo del mes como si estuviera cerrado.
INCOMPLETE_DATA_THRESHOLD_DAYS = 3


def _month_range(year: int, month: int) -> tuple[date, date]:
    range_start = date(year, month, 1)
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    range_end = date(next_year, next_month, 1)
    return range_start, range_end


@router.get("/summary", response_model=DashboardSummary)
def monthly_dashboard(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    year: Annotated[int, Query(ge=2000, le=2100)],
    month: Annotated[int, Query(ge=1, le=12)],
    account_id: int | None = None,
) -> DashboardSummary:
    range_start, range_end = _month_range(year, month)

    if account_id is not None:
        owned = (
            db.query(Account.id)
            .filter(Account.id == account_id, Account.owner_id == current_user.id)
            .first()
        )
        if owned is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada")

    base_filter = (
        Transaction.owner_id == current_user.id,
        Transaction.deleted_at.is_(None),
        Transaction.posted_at >= range_start,
        Transaction.posted_at < range_end,
    )
    if account_id is not None:
        base_filter = (*base_filter, Transaction.account_id == account_id)

    income_total = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(*base_filter, Transaction.direction == "income")
        .scalar()
    ) or Decimal("0")
    expense_total = (
        db.query(func.coalesce(func.sum(-Transaction.amount), 0))
        .filter(*base_filter, Transaction.direction == "expense")
        .scalar()
    ) or Decimal("0")
    net_total = income_total - expense_total
    net_status: str = "a_favor" if net_total >= 0 else "en_contra"

    # Roll-up gasto: subcategoría -> categoría principal, siempre vía la
    # subcategoría (las transacciones nunca apuntan a la raíz directamente).
    Sub = aliased(Category)
    Root = aliased(Category)
    rows = (
        db.query(
            Root.id,
            Root.name,
            Root.icon,
            Root.color,
            Sub.id,
            Sub.name,
            Sub.is_fixed,
            func.sum(-Transaction.amount),
        )
        .join(Sub, Transaction.category_id == Sub.id)
        .join(Root, Sub.parent_id == Root.id)
        .filter(*base_filter, Transaction.direction == "expense")
        .group_by(Root.id, Root.name, Root.icon, Root.color, Sub.id, Sub.name, Sub.is_fixed)
        .all()
    )

    roots: dict[int, DashboardCategoryNode] = {}
    root_order: list[int] = []
    fixed_total = Decimal("0")
    for root_id, root_name, icon, color, sub_id, sub_name, is_fixed, sub_total in rows:
        if root_id not in roots:
            roots[root_id] = DashboardCategoryNode(
                category_id=root_id,
                category_name=root_name,
                icon=icon,
                color=color,
                total=Decimal("0"),
                subcategories=[],
            )
            root_order.append(root_id)
        node = roots[root_id]
        node.total += sub_total
        node.subcategories.append(
            CategorySummary(category_id=sub_id, category_name=sub_name, total=sub_total)
        )
        if is_fixed:
            fixed_total += sub_total

    by_category = [roots[root_id] for root_id in root_order]
    by_category.sort(key=lambda node: node.total, reverse=True)
    for node in by_category:
        node.subcategories.sort(key=lambda s: s.total, reverse=True)
    variable_total = expense_total - fixed_total

    last_transaction_date = (
        db.query(func.max(Transaction.posted_at))
        .filter(*base_filter, Transaction.direction.in_(("income", "expense")))
        .scalar()
    )

    today = date.today()
    is_current_month = (year, month) == (today.year, today.month)
    incomplete_data = is_current_month and (
        last_transaction_date is None
        or (today - last_transaction_date).days > INCOMPLETE_DATA_THRESHOLD_DAYS
    )

    return DashboardSummary(
        year=year,
        month=month,
        income_total=income_total,
        expense_total=expense_total,
        net_total=net_total,
        net_status=net_status,
        fixed_total=fixed_total,
        variable_total=variable_total,
        by_category=by_category,
        incomplete_data=incomplete_data,
        last_transaction_date=last_transaction_date,
    )
