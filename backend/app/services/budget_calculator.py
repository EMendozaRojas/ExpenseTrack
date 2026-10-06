"""Resolución y cálculo de presupuestos mensuales.

El presupuesto de una categoría en un mes se resuelve así (design D1):
un `BudgetMonth` de ese mes gana (`skip` = no hay presupuesto); si no, la
serie (`Budget`) que cubre el mes; si no, no hay presupuesto.

Lo comparten el router de presupuestos, las notificaciones y el
recomendador. `today()` es el único punto que lee el reloj, para que los
tests puedan fijar el "mes en curso".
"""

import calendar
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.budget import Budget
from app.models.budget_month import BudgetMonth
from app.models.category import Category
from app.models.transaction import Transaction

WARNING_THRESHOLD_PCT = 80
EXCEEDED_THRESHOLD_PCT = 100
PACE_MIN_ELAPSED_DAYS = 5


def today() -> date:
    return date.today()


def current_month() -> date:
    return today().replace(day=1)


def add_months(month: date, n: int) -> date:
    index = month.year * 12 + (month.month - 1) + n
    return date(index // 12, index % 12 + 1, 1)


def month_key(month: date) -> str:
    return f"{month.year:04d}-{month.month:02d}"


def parse_month_key(key: str) -> date:
    year, month = key.split("-")
    return date(int(year), int(month), 1)


def series_covers(series: Budget, month: date) -> bool:
    return series.starts_on <= month and (series.ends_on is None or month < series.ends_on)


@dataclass
class ResolvedBudget:
    category_id: int | None
    category_name: str
    category: Category | None
    month: date
    amount: Decimal
    source: str  # "series" | "override" | "single"
    series: Budget | None
    entry: BudgetMonth | None

    @property
    def repeats(self) -> bool:
        return self.series is not None

    @property
    def frozen_spent(self) -> Decimal | None:
        return self.entry.frozen_spent if self.entry is not None else None


@dataclass
class Pace:
    projected: Decimal
    will_exceed: bool


@dataclass
class BudgetEvaluation:
    budget: ResolvedBudget
    spent: Decimal
    pct: float
    status: str
    pace: Pace | None


def _series_for(
    db: Session, owner_id: int, month: date, category_id: int | None = None
) -> list[Budget]:
    query = db.query(Budget).filter(
        Budget.owner_id == owner_id,
        Budget.starts_on <= month,
        or_(Budget.ends_on.is_(None), Budget.ends_on > month),
    )
    if category_id is not None:
        query = query.filter(Budget.category_id == category_id)
    return query.all()


def _resolve(
    series: Budget | None, entry: BudgetMonth | None, month: date
) -> ResolvedBudget | None:
    if entry is not None:
        if entry.kind == "skip" or entry.amount is None:
            return None
        return ResolvedBudget(
            category_id=entry.category_id,
            category_name=entry.category.name if entry.category else entry.category_name,
            category=entry.category,
            month=month,
            amount=entry.amount,
            # Un `override` sin serie que lo cubra se comporta como un mes suelto.
            source="override" if series is not None else "single",
            series=series,
            entry=entry,
        )
    if series is not None:
        return ResolvedBudget(
            category_id=series.category_id,
            category_name=series.category.name if series.category else series.category_name,
            category=series.category,
            month=month,
            amount=series.amount,
            source="series",
            series=series,
            entry=None,
        )
    return None


def resolve_month(db: Session, owner_id: int, month: date) -> list[ResolvedBudget]:
    series_by_category = {
        s.category_id: s for s in _series_for(db, owner_id, month) if s.category_id is not None
    }
    entries = (
        db.query(BudgetMonth)
        .filter(BudgetMonth.owner_id == owner_id, BudgetMonth.month == month)
        .all()
    )
    entries_by_category = {e.category_id: e for e in entries if e.category_id is not None}

    resolved: list[ResolvedBudget] = []
    for category_id in series_by_category.keys() | entries_by_category.keys():
        budget = _resolve(
            series_by_category.get(category_id), entries_by_category.get(category_id), month
        )
        if budget is not None:
            resolved.append(budget)
    # Meses conservados de categorías ya borradas (design D8).
    for entry in entries:
        if entry.category_id is None:
            budget = _resolve(None, entry, month)
            if budget is not None:
                resolved.append(budget)
    resolved.sort(key=lambda b: b.category_name.lower())
    return resolved


def resolve_one(db: Session, owner_id: int, category_id: int, month: date) -> ResolvedBudget | None:
    series = next(iter(_series_for(db, owner_id, month, category_id)), None)
    entry = (
        db.query(BudgetMonth)
        .filter(
            BudgetMonth.owner_id == owner_id,
            BudgetMonth.category_id == category_id,
            BudgetMonth.month == month,
        )
        .first()
    )
    return _resolve(series, entry, month)


def subtree_ids(db: Session, categories: list[Category]) -> dict[int, list[int]]:
    """Ids que cuentan para el `spent` de cada categoría: una raíz incluye sus
    subcategorías; una subcategoría, solo ella."""
    root_ids = [c.id for c in categories if c.parent_id is None]
    children: dict[int, list[int]] = {root_id: [] for root_id in root_ids}
    if root_ids:
        for child_id, parent_id in (
            db.query(Category.id, Category.parent_id).filter(Category.parent_id.in_(root_ids)).all()
        ):
            children[parent_id].append(child_id)
    return {c.id: [c.id, *children.get(c.id, [])] for c in categories}


def spent_by_category_and_month(
    db: Session, owner_id: int, category_ids: list[int], start: date, end: date
) -> dict[tuple[int, date], Decimal]:
    """Gasto por (categoría hoja, mes) en [start, end), en una sola consulta."""
    if not category_ids:
        return {}
    month_col = func.date_trunc("month", Transaction.posted_at)
    rows = (
        db.query(Transaction.category_id, month_col, func.sum(-Transaction.amount))
        .filter(
            Transaction.owner_id == owner_id,
            Transaction.deleted_at.is_(None),
            Transaction.direction == "expense",
            Transaction.category_id.in_(category_ids),
            Transaction.posted_at >= start,
            Transaction.posted_at < end,
        )
        .group_by(Transaction.category_id, month_col)
        .all()
    )
    result: dict[tuple[int, date], Decimal] = {}
    for category_id, month_value, total in rows:
        month = month_value.date() if hasattr(month_value, "date") else month_value
        result[(category_id, month.replace(day=1))] = Decimal(total or 0)
    return result


def compute_pace(spent: Decimal, amount: Decimal, month: date) -> Pace | None:
    now = today()
    if month != now.replace(day=1) or now.day <= PACE_MIN_ELAPSED_DAYS:
        return None
    days_in_month = calendar.monthrange(month.year, month.month)[1]
    projected = (spent / now.day * days_in_month).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return Pace(projected=projected, will_exceed=projected >= amount)


def status_for(pct: float) -> str:
    if pct >= EXCEEDED_THRESHOLD_PCT:
        return "exceeded"
    if pct >= WARNING_THRESHOLD_PCT:
        return "warning"
    return "ok"


def evaluate(
    db: Session, owner_id: int, budgets: list[ResolvedBudget], month: date
) -> list[BudgetEvaluation]:
    live = [b for b in budgets if b.frozen_spent is None and b.category is not None]
    ids_by_category = subtree_ids(db, [b.category for b in live if b.category is not None])
    all_ids = sorted({cid for ids in ids_by_category.values() for cid in ids})
    spent_map = spent_by_category_and_month(db, owner_id, all_ids, month, add_months(month, 1))

    evaluations: list[BudgetEvaluation] = []
    for budget in budgets:
        if budget.frozen_spent is not None:
            spent = budget.frozen_spent
        elif budget.category_id is not None:
            spent = sum(
                (
                    spent_map.get((cid, month), Decimal("0"))
                    for cid in ids_by_category[budget.category_id]
                ),
                Decimal("0"),
            )
        else:
            spent = Decimal("0")
        spent = spent.quantize(Decimal("0.01"))
        pct = float(spent / budget.amount * 100) if budget.amount else 0.0
        evaluations.append(
            BudgetEvaluation(
                budget=budget,
                spent=spent,
                pct=round(pct, 1),
                status=status_for(pct),
                pace=compute_pace(spent, budget.amount, month),
            )
        )
    return evaluations


def evaluate_month(db: Session, owner_id: int, month: date) -> list[BudgetEvaluation]:
    return evaluate(db, owner_id, resolve_month(db, owner_id, month), month)
