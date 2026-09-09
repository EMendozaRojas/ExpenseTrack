from datetime import date, timedelta
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.category import Category
from app.models.dismissed_recurring_series import DismissedRecurringSeries
from app.models.insight_settings import InsightSettings
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.insights import (
    AntSpendingGroup,
    DismissRequest,
    InsightSettingsRead,
    InsightSettingsUpdate,
    RecurringSeriesRead,
)
from app.services.recurring_detector import detect_recurring_series

router = APIRouter(prefix="/insights", tags=["insights"])

RECURRING_WINDOW_MONTHS = 6


def _get_or_create_settings(db: Session, current_user: User) -> InsightSettings:
    settings = db.query(InsightSettings).filter(InsightSettings.owner_id == current_user.id).first()
    if settings is None:
        settings = InsightSettings(owner_id=current_user.id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def _month_range(year: int, month: int) -> tuple[date, date]:
    range_start = date(year, month, 1)
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    return range_start, date(next_year, next_month, 1)


@router.get("/recurring", response_model=list[RecurringSeriesRead])
def list_recurring_series(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[RecurringSeriesRead]:
    window_start = date.today() - timedelta(days=30 * RECURRING_WINDOW_MONTHS)
    transactions = (
        db.query(Transaction)
        .options(joinedload(Transaction.category))
        .filter(
            Transaction.owner_id == current_user.id,
            Transaction.deleted_at.is_(None),
            Transaction.direction.in_(("income", "expense")),
            Transaction.posted_at >= window_start,
        )
        .all()
    )
    series = detect_recurring_series(transactions)

    dismissed_keys = {
        row.series_key
        for row in db.query(DismissedRecurringSeries.series_key).filter(
            DismissedRecurringSeries.owner_id == current_user.id
        )
    }

    return [
        RecurringSeriesRead(
            key=s.key,
            label=s.label,
            direction=s.direction,
            category_id=s.category_id,
            category_name=s.category_name,
            occurrences=s.occurrences,
            avg_amount=s.avg_amount,
            cadence_days=s.cadence_days,
            cadence_label=s.cadence_label,
            first_posted_at=s.first_posted_at,
            last_posted_at=s.last_posted_at,
            dismissed=s.key in dismissed_keys,
        )
        for s in series
    ]


@router.post("/recurring/dismiss", status_code=status.HTTP_204_NO_CONTENT)
def dismiss_recurring_series(
    payload: DismissRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    existing = (
        db.query(DismissedRecurringSeries)
        .filter(
            DismissedRecurringSeries.owner_id == current_user.id,
            DismissedRecurringSeries.series_key == payload.series_key,
        )
        .first()
    )
    if existing is None:
        db.add(DismissedRecurringSeries(owner_id=current_user.id, series_key=payload.series_key))
        db.commit()


@router.post("/recurring/restore", status_code=status.HTTP_204_NO_CONTENT)
def restore_recurring_series(
    payload: DismissRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    db.query(DismissedRecurringSeries).filter(
        DismissedRecurringSeries.owner_id == current_user.id,
        DismissedRecurringSeries.series_key == payload.series_key,
    ).delete()
    db.commit()


@router.get("/ant-spending", response_model=list[AntSpendingGroup])
def ant_spending(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    year: Annotated[int, Query(ge=2000, le=2100)],
    month: Annotated[int, Query(ge=1, le=12)],
) -> list[AntSpendingGroup]:
    settings = _get_or_create_settings(db, current_user)
    range_start, range_end = _month_range(year, month)

    rows = (
        db.query(
            Category.id,
            Category.name,
            func.count(Transaction.id),
            func.sum(-Transaction.amount),
        )
        .join(Category, Transaction.category_id == Category.id)
        .filter(
            Transaction.owner_id == current_user.id,
            Transaction.deleted_at.is_(None),
            Transaction.direction == "expense",
            Transaction.posted_at >= range_start,
            Transaction.posted_at < range_end,
            (-Transaction.amount) <= settings.ant_max_amount,
        )
        .group_by(Category.id, Category.name)
        .all()
    )

    groups = [
        AntSpendingGroup(
            category_id=category_id,
            category_name=category_name,
            occurrences=count,
            aggregate=aggregate,
            avg_amount=(aggregate / count).quantize(Decimal("0.01")),
        )
        for category_id, category_name, count, aggregate in rows
        if count >= settings.ant_min_occurrences and aggregate >= settings.ant_min_aggregate
    ]
    groups.sort(key=lambda g: g.aggregate, reverse=True)
    return groups


@router.get("/settings", response_model=InsightSettingsRead)
def get_settings(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> InsightSettingsRead:
    return InsightSettingsRead.model_validate(_get_or_create_settings(db, current_user))


@router.patch("/settings", response_model=InsightSettingsRead)
def update_settings(
    payload: InsightSettingsUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> InsightSettingsRead:
    settings = _get_or_create_settings(db, current_user)
    if payload.ant_max_amount is not None:
        settings.ant_max_amount = payload.ant_max_amount
    if payload.ant_min_occurrences is not None:
        settings.ant_min_occurrences = payload.ant_min_occurrences
    if payload.ant_min_aggregate is not None:
        settings.ant_min_aggregate = payload.ant_min_aggregate
    db.commit()
    db.refresh(settings)
    return InsightSettingsRead.model_validate(settings)
