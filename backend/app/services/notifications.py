"""Genera notificaciones de presupuestos y metas.

Igual que el purgado de la papelera, no hay scheduler en este proyecto: se
dispara de forma perezosa (síncrona) justo después de las acciones que
pueden cruzar un umbral — crear/editar/borrar un movimiento (presupuestos) o
agregar una aportación (metas) — en vez de un job periódico.
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.budget import Budget
from app.models.category import Category
from app.models.goal_contribution import GoalContribution
from app.models.notification import Notification
from app.models.savings_goal import SavingsGoal
from app.models.transaction import Transaction
from app.models.user import User
from app.services.email import send_email

BUDGET_WARNING_THRESHOLD_PCT = 80
BUDGET_EXCEEDED_THRESHOLD_PCT = 100
GOAL_NEAR_THRESHOLD_PCT = 80


def _month_range(year: int, month: int) -> tuple[date, date]:
    range_start = date(year, month, 1)
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    return range_start, date(next_year, next_month, 1)


def _create_if_missing(
    db: Session,
    current_user: User,
    notification_type: str,
    related_id: int,
    period_key: str,
    title: str,
    body: str,
) -> None:
    existing = (
        db.query(Notification)
        .filter(
            Notification.owner_id == current_user.id,
            Notification.type == notification_type,
            Notification.related_id == related_id,
            Notification.period_key == period_key,
        )
        .first()
    )
    if existing is not None:
        return
    db.add(
        Notification(
            owner_id=current_user.id,
            type=notification_type,
            related_id=related_id,
            period_key=period_key,
            title=title,
            body=body,
        )
    )
    db.commit()
    send_email(current_user.email, title, body)


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


def check_budget_notifications(db: Session, current_user: User) -> None:
    today = date.today()
    range_start, range_end = _month_range(today.year, today.month)
    period_key = f"{today.year:04d}-{today.month:02d}"

    budgets = (
        db.query(Budget)
        .filter(Budget.owner_id == current_user.id, Budget.is_active.is_(True))
        .all()
    )
    for budget in budgets:
        if not budget.amount:
            continue
        spent = _spent_for_category(db, budget.category, current_user.id, range_start, range_end)
        pct = float(spent / budget.amount * 100)

        if pct >= BUDGET_EXCEEDED_THRESHOLD_PCT:
            _create_if_missing(
                db,
                current_user,
                "budget_exceeded",
                budget.id,
                period_key,
                f"Presupuesto superado: {budget.category.name}",
                f'Ya gastaste {spent:.2f} de {budget.amount:.2f} en "{budget.category.name}" '
                f"este mes ({pct:.0f}%).",
            )
        elif pct >= BUDGET_WARNING_THRESHOLD_PCT:
            _create_if_missing(
                db,
                current_user,
                "budget_warning",
                budget.id,
                period_key,
                f"Cerca del límite: {budget.category.name}",
                f'Vas en {spent:.2f} de {budget.amount:.2f} en "{budget.category.name}" este mes '
                f"({pct:.0f}%).",
            )


def check_goal_notifications(db: Session, current_user: User, goal: SavingsGoal) -> None:
    if not goal.target_amount:
        return

    current_amount: Decimal = (
        db.query(func.coalesce(func.sum(GoalContribution.amount), 0))
        .filter(GoalContribution.goal_id == goal.id)
        .scalar()
        or Decimal("0")
    )
    pct = float(current_amount / goal.target_amount * 100)

    if pct >= 100:
        _create_if_missing(
            db,
            current_user,
            "goal_reached",
            goal.id,
            "",
            f"¡Meta alcanzada!: {goal.name}",
            f'Llegaste a tu meta "{goal.name}" ({current_amount:.2f} de {goal.target_amount:.2f}).',
        )
    elif pct >= GOAL_NEAR_THRESHOLD_PCT:
        _create_if_missing(
            db,
            current_user,
            "goal_near",
            goal.id,
            "",
            f"Cerca de tu meta: {goal.name}",
            f'Vas en {current_amount:.2f} de {goal.target_amount:.2f} en "{goal.name}" ({pct:.0f}%).',
        )
