"""Genera notificaciones de presupuestos y metas.

Igual que el purgado de la papelera, no hay scheduler en este proyecto: se
dispara de forma perezosa (síncrona) justo después de las acciones que
pueden cruzar un umbral — cambios en movimientos, importaciones o
presupuestos (presupuestos) o agregar una aportación (metas) — y además cada
vez que el usuario entra a la app (`POST /notifications/check`).
"""

from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.goal_contribution import GoalContribution
from app.models.notification import Notification
from app.models.savings_goal import SavingsGoal
from app.models.user import User
from app.services import budget_calculator as calc
from app.services.email import send_email

GOAL_NEAR_THRESHOLD_PCT = 80
BODY_MAX_LENGTH = 500

MONTH_NAMES = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)


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
            body=body[:BODY_MAX_LENGTH],
        )
    )
    try:
        db.commit()
    except IntegrityError:
        # Dos peticiones simultáneas (p. ej. la revisión al entrar y otra
        # acción) pueden llegar aquí a la vez: la UNIQUE de la tabla decide.
        db.rollback()
        return
    send_email(current_user.email, title, body)


def check_budget_notifications(db: Session, current_user: User) -> None:
    """Avisos al 80% y 100% de los presupuestos del mes en curso, uno por
    (categoría, tipo, mes). Los meses pasados nunca avisan."""
    month = calc.current_month()
    period_key = calc.month_key(month)

    for evaluation in calc.evaluate_month(db, current_user.id, month):
        budget = evaluation.budget
        if budget.category_id is None:
            continue
        pct = evaluation.pct
        if evaluation.status == "exceeded":
            _create_if_missing(
                db,
                current_user,
                "budget_exceeded",
                budget.category_id,
                period_key,
                f"Presupuesto superado: {budget.category_name}",
                f"Ya gastaste {evaluation.spent:.2f} de {budget.amount:.2f} "
                f'en "{budget.category_name}" este mes ({pct:.0f}%).',
            )
        elif evaluation.status == "warning":
            _create_if_missing(
                db,
                current_user,
                "budget_warning",
                budget.category_id,
                period_key,
                f"Cerca del límite: {budget.category_name}",
                f"Vas en {evaluation.spent:.2f} de {budget.amount:.2f} "
                f'en "{budget.category_name}" este mes ({pct:.0f}%).',
            )


def create_month_summary(db: Session, current_user: User) -> None:
    """Resumen de cierre del mes anterior (design D5): una sola vez, y solo si
    ese mes tuvo presupuestos."""
    previous = calc.add_months(calc.current_month(), -1)
    evaluations = calc.evaluate_month(db, current_user.id, previous)
    if not evaluations:
        return

    kept = sum(1 for e in evaluations if e.status != "exceeded")
    total = len(evaluations)
    month_name = MONTH_NAMES[previous.month - 1]
    exceeded = [e for e in evaluations if e.status == "exceeded"]
    body = f"En {month_name} cumpliste {kept} de {total} presupuestos."
    if exceeded:
        body += " Excedidos: " + ", ".join(
            f"{e.budget.category_name} ({e.pct:.0f}%)" for e in exceeded
        ) + "."
    _create_if_missing(
        db,
        current_user,
        "budget_month_summary",
        0,
        calc.month_key(previous),
        f"Resumen de {month_name}: {kept} de {total} presupuestos cumplidos",
        body,
    )


def notify_budget_category_deleted(
    db: Session, current_user: User, category_id: int, category_name: str
) -> None:
    _create_if_missing(
        db,
        current_user,
        "budget_category_deleted",
        category_id,
        "",
        f"Presupuesto finalizado: {category_name}",
        f'Borraste la categoría "{category_name}". Su presupuesto deja de aplicar desde este mes; '
        "los meses anteriores conservan su historial.",
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
