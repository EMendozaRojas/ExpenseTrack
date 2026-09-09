from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.models.budget import Budget
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.user import User
from app.core.database import get_db
from app.schemas.budget import BudgetCreate, BudgetRead, BudgetStatus, BudgetUpdate

router = APIRouter(prefix="/budgets", tags=["budgets"])

WARNING_THRESHOLD_PCT = 80
EXCEEDED_THRESHOLD_PCT = 100


def _visible_expense_category(db: Session, category_id: int, current_user: User) -> Category:
    category = (
        db.query(Category)
        .filter(
            Category.id == category_id,
            Category.kind == "expense",
            or_(Category.owner_id.is_(None), Category.owner_id == current_user.id),
        )
        .first()
    )
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Categoría de gasto no encontrada"
        )
    return category


def _get_owned_budget(db: Session, budget_id: int, current_user: User) -> Budget:
    budget = (
        db.query(Budget)
        .filter(Budget.id == budget_id, Budget.owner_id == current_user.id)
        .first()
    )
    if budget is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presupuesto no encontrado")
    return budget


def _spent_for_category(
    db: Session, category: Category, owner_id: int, range_start: date, range_end: date
) -> Decimal:
    category_ids = [category.id]
    if category.parent_id is None:
        children = db.query(Category.id).filter(Category.parent_id == category.id).all()
        category_ids += [c.id for c in children]

    spent: Decimal | None = (
        db.query(func.coalesce(func.sum(-Transaction.amount), 0))
        .filter(
            Transaction.owner_id == owner_id,
            Transaction.deleted_at.is_(None),
            Transaction.direction == "expense",
            Transaction.category_id.in_(category_ids),
            Transaction.posted_at >= range_start,
            Transaction.posted_at < range_end,
        )
        .scalar()
    )
    return spent or Decimal("0")


def _month_range(year: int, month: int) -> tuple[date, date]:
    range_start = date(year, month, 1)
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    return range_start, date(next_year, next_month, 1)


def _to_read(budget: Budget) -> BudgetRead:
    return BudgetRead(
        id=budget.id,
        category_id=budget.category_id,
        category_name=budget.category.name,
        amount=budget.amount,
        is_active=budget.is_active,
        created_at=budget.created_at,
    )


@router.get("/", response_model=list[BudgetStatus])
def list_budgets(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    year: Annotated[int, Query(ge=2000, le=2100)],
    month: Annotated[int, Query(ge=1, le=12)],
) -> list[BudgetStatus]:
    range_start, range_end = _month_range(year, month)
    budgets = (
        db.query(Budget)
        .filter(Budget.owner_id == current_user.id)
        .order_by(Budget.created_at)
        .all()
    )

    results: list[BudgetStatus] = []
    for budget in budgets:
        spent = _spent_for_category(db, budget.category, current_user.id, range_start, range_end)
        pct = float(spent / budget.amount * 100) if budget.amount else 0.0
        budget_status: str = (
            "exceeded"
            if pct >= EXCEEDED_THRESHOLD_PCT
            else "warning"
            if pct >= WARNING_THRESHOLD_PCT
            else "ok"
        )
        results.append(
            BudgetStatus(
                id=budget.id,
                category_id=budget.category_id,
                category_name=budget.category.name,
                category_icon=budget.category.icon,
                amount=budget.amount,
                is_active=budget.is_active,
                spent=spent,
                pct=round(pct, 1),
                status=budget_status,
            )
        )
    return results


@router.post("/", response_model=BudgetRead, status_code=status.HTTP_201_CREATED)
def create_budget(
    payload: BudgetCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> BudgetRead:
    _visible_expense_category(db, payload.category_id, current_user)

    existing = (
        db.query(Budget)
        .filter(Budget.owner_id == current_user.id, Budget.category_id == payload.category_id)
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un presupuesto para esta categoría",
        )

    budget = Budget(owner_id=current_user.id, category_id=payload.category_id, amount=payload.amount)
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return _to_read(budget)


@router.patch("/{budget_id}", response_model=BudgetRead)
def update_budget(
    budget_id: int,
    payload: BudgetUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> BudgetRead:
    budget = _get_owned_budget(db, budget_id, current_user)
    if payload.amount is not None:
        budget.amount = payload.amount
    if payload.is_active is not None:
        budget.is_active = payload.is_active
    db.commit()
    db.refresh(budget)
    return _to_read(budget)


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    budget = _get_owned_budget(db, budget_id, current_user)
    db.delete(budget)
    db.commit()
