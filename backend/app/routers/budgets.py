from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.category import Category
from app.models.user import User
from app.schemas.budget import (
    BudgetCreate,
    BudgetPace,
    BudgetRecommendation,
    BudgetStatus,
    BudgetUpdate,
    CopyPreviewItem,
    CopyRequest,
    CopyResult,
    MonthlySpent,
    PlannedMonthRead,
    RecommendationBasis,
    Scope,
)
from app.services import budget_calculator as calc
from app.services import budget_operations as ops
from app.services.budget_recommender import recommend
from app.services.notifications import check_budget_notifications

router = APIRouter(prefix="/budgets", tags=["budgets"])

PeriodParam = Annotated[str, Path(pattern=r"^\d{4}-(0[1-9]|1[0-2])$", description="Mes YYYY-MM")]
YearQuery = Annotated[int, Query(ge=2000, le=2100)]
MonthQuery = Annotated[int, Query(ge=1, le=12)]


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


def _raise_http(error: ops.BudgetError) -> None:
    code = (
        status.HTTP_404_NOT_FOUND
        if isinstance(error, ops.BudgetNotFound)
        else status.HTTP_409_CONFLICT
    )
    raise HTTPException(status_code=code, detail=str(error)) from error


def _to_status(evaluation: calc.BudgetEvaluation) -> BudgetStatus:
    budget = evaluation.budget
    return BudgetStatus(
        category_id=budget.category_id,
        category_name=budget.category_name,
        category_icon=budget.category.icon if budget.category else None,
        month=calc.month_key(budget.month),
        amount=budget.amount,
        repeats=budget.repeats,
        source=budget.source,
        editable=budget.month >= calc.current_month() and budget.category_id is not None,
        spent=evaluation.spent,
        pct=evaluation.pct,
        status=evaluation.status,
        pace=(
            BudgetPace(projected=evaluation.pace.projected, will_exceed=evaluation.pace.will_exceed)
            if evaluation.pace
            else None
        ),
    )


def _status_for(db: Session, owner_id: int, category_id: int, month: date) -> BudgetStatus:
    resolved = calc.resolve_one(db, owner_id, category_id, month)
    assert resolved is not None
    return _to_status(calc.evaluate(db, owner_id, [resolved], month)[0])


@router.get("/", response_model=list[BudgetStatus])
def list_budgets(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    year: YearQuery,
    month: MonthQuery,
) -> list[BudgetStatus]:
    return [_to_status(e) for e in calc.evaluate_month(db, current_user.id, date(year, month, 1))]


@router.post("/", response_model=BudgetStatus, status_code=status.HTTP_201_CREATED)
def create_budget(
    payload: BudgetCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> BudgetStatus:
    category = _visible_expense_category(db, payload.category_id, current_user)
    month = date(payload.year, payload.month, 1)
    try:
        ops.create(db, current_user.id, category, month, payload.amount, payload.repeat)
    except ops.BudgetError as error:
        _raise_http(error)
    check_budget_notifications(db, current_user)
    return _status_for(db, current_user.id, category.id, month)


@router.get("/recommendations", response_model=list[BudgetRecommendation])
def list_recommendations(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    category_id: int | None = None,
) -> list[BudgetRecommendation]:
    return [
        BudgetRecommendation(
            category_id=r.category.id,
            category_name=r.category.name,
            parent_id=r.category.parent_id,
            flag=r.flag,
            suggested_amount=r.suggested_amount,
            current_amount=r.current_amount,
            basis=RecommendationBasis(
                months=[MonthlySpent(month=calc.month_key(m), spent=v) for m, v in r.monthly_spent],
                mean=r.mean,
                same_month_last_year=r.same_month_last_year,
                share_pct=r.share_pct,
                over_typical=r.over_typical,
            ),
        )
        for r in recommend(db, current_user.id, category_id)
    ]


@router.get("/copy-preview", response_model=list[CopyPreviewItem])
def copy_preview(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    year: YearQuery,
    month: MonthQuery,
) -> list[CopyPreviewItem]:
    target = date(year, month, 1)
    if target < calc.current_month():
        return []
    return [
        CopyPreviewItem(category_id=b.category_id, category_name=b.category_name, amount=b.amount)
        for b in ops.copy_preview(db, current_user.id, target)
        if b.category_id is not None
    ]


@router.post("/copy", response_model=CopyResult)
def copy_budgets(
    payload: CopyRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CopyResult:
    items = [
        (_visible_expense_category(db, item.category_id, current_user), item.amount)
        for item in payload.items
    ]
    try:
        created, skipped = ops.copy(
            db, current_user.id, date(payload.year, payload.month, 1), items
        )
    except ops.BudgetError as error:
        _raise_http(error)
    check_budget_notifications(db, current_user)
    return CopyResult(created=created, skipped=skipped)


@router.get("/{category_id}/planned", response_model=list[PlannedMonthRead])
def planned_months(
    category_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    from_: Annotated[str, Query(alias="from", pattern=r"^\d{4}-(0[1-9]|1[0-2])$")],
) -> list[PlannedMonthRead]:
    _visible_expense_category(db, category_id, current_user)
    return [
        PlannedMonthRead(month=calc.month_key(p.month), amount=p.amount, kind=p.kind)
        for p in ops.planned_after(db, current_user.id, category_id, calc.parse_month_key(from_))
    ]


@router.put("/{category_id}/{period}", response_model=BudgetStatus)
def update_budget(
    category_id: int,
    period: PeriodParam,
    payload: BudgetUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> BudgetStatus:
    category = _visible_expense_category(db, category_id, current_user)
    month = calc.parse_month_key(period)
    try:
        ops.update(
            db, current_user.id, category, month, payload.amount, payload.scope, payload.repeat
        )
    except ops.BudgetError as error:
        _raise_http(error)
    check_budget_notifications(db, current_user)
    return _status_for(db, current_user.id, category.id, month)


@router.delete("/{category_id}/{period}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    category_id: int,
    period: PeriodParam,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    scope: Scope = "this",
) -> None:
    category = _visible_expense_category(db, category_id, current_user)
    try:
        ops.delete(db, current_user.id, category, calc.parse_month_key(period), scope)
    except ops.BudgetError as error:
        _raise_http(error)
    check_budget_notifications(db, current_user)
