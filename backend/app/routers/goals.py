import math
from datetime import UTC, date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.core.openapi import AUTH_RESPONSES, Tag, error_responses
from app.models.account import Account
from app.models.goal_contribution import GoalContribution
from app.models.savings_goal import SavingsGoal
from app.models.user import User
from app.schemas.goal import (
    ContributionCreate,
    ContributionRead,
    GoalCreate,
    GoalProjection,
    GoalRead,
    GoalUpdate,
)
from app.services.notifications import check_goal_notifications

router = APIRouter(prefix="/goals", tags=[Tag.METAS], responses=AUTH_RESPONSES)

GoalId = Annotated[int, Path(description="Id de la meta.", examples=[222])]
_GOAL_NOT_FOUND = error_responses(
    404, e404=("La meta no existe o es de otro usuario.", "Meta no encontrada")
)
_ACCOUNT_NOT_FOUND = "La meta, o la cuenta vinculada, no existe o es de otro usuario."

PROJECTION_WINDOW_MONTHS = 3
_DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def _is_leap(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def _add_months(base: date, months: int) -> date:
    month_index = base.month - 1 + months
    year = base.year + month_index // 12
    month = month_index % 12 + 1
    max_day = _DAYS_IN_MONTH[month - 1]
    if month == 2 and _is_leap(year):
        max_day = 29
    return date(year, month, min(base.day, max_day))


def _month_start(year: int, month: int) -> date:
    return date(year, month, 1)


def _full_months_before(today: date, count: int) -> list[tuple[date, date]]:
    """Los `count` meses calendario completos inmediatamente anteriores al
    actual, más antiguo primero, como pares (inicio, fin_exclusivo)."""
    months = []
    year, month = today.year, today.month
    for _ in range(count):
        month -= 1
        if month == 0:
            month, year = 12, year - 1
        start = _month_start(year, month)
        next_month = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1
        months.append((start, _month_start(next_year, next_month)))
    return list(reversed(months))


def _get_owned_goal(db: Session, goal_id: int, current_user: User) -> SavingsGoal:
    goal = (
        db.query(SavingsGoal)
        .filter(SavingsGoal.id == goal_id, SavingsGoal.owner_id == current_user.id)
        .first()
    )
    if goal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meta no encontrada")
    return goal


def _current_amount(db: Session, goal_id: int) -> Decimal:
    total = (
        db.query(func.coalesce(func.sum(GoalContribution.amount), 0))
        .filter(GoalContribution.goal_id == goal_id)
        .scalar()
    )
    return total or Decimal("0")


def _to_read(db: Session, goal: SavingsGoal) -> GoalRead:
    current = _current_amount(db, goal.id)
    pct = float(current / goal.target_amount * 100) if goal.target_amount else 0.0
    return GoalRead(
        id=goal.id,
        name=goal.name,
        target_amount=goal.target_amount,
        target_date=goal.target_date,
        linked_account_id=goal.linked_account_id,
        status=goal.status,
        current_amount=current,
        pct=round(pct, 1),
        created_at=goal.created_at,
    )


@router.get("/", response_model=list[GoalRead], summary="Listar metas")
def list_goals(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[GoalRead]:
    """Metas del usuario, de la más antigua a la más reciente, con lo
    aportado y el porcentaje de avance."""
    goals = (
        db.query(SavingsGoal)
        .filter(SavingsGoal.owner_id == current_user.id)
        .order_by(SavingsGoal.created_at)
        .all()
    )
    return [_to_read(db, goal) for goal in goals]


@router.post(
    "/",
    response_model=GoalRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear meta",
    responses=error_responses(
        404, e404=("La cuenta vinculada no existe o es de otro usuario.", "Cuenta no encontrada")
    ),
)
def create_goal(
    payload: GoalCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> GoalRead:
    """Crea una meta activa sin aportaciones. La cuenta vinculada es solo
    informativa: el progreso sale de las aportaciones, no del saldo."""
    if payload.linked_account_id is not None:
        account = (
            db.query(Account)
            .filter(Account.id == payload.linked_account_id, Account.owner_id == current_user.id)
            .first()
        )
        if account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada"
            )

    goal = SavingsGoal(
        owner_id=current_user.id,
        name=payload.name,
        target_amount=payload.target_amount,
        target_date=payload.target_date,
        linked_account_id=payload.linked_account_id,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return _to_read(db, goal)


@router.patch(
    "/{goal_id}",
    response_model=GoalRead,
    summary="Editar meta",
    responses=error_responses(404, e404=_ACCOUNT_NOT_FOUND),
)
def update_goal(
    goal_id: GoalId,
    payload: GoalUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> GoalRead:
    """Cambia los campos enviados; el resto no cambia. Permite archivar la
    meta (`status: archived`). Los campos opcionales no se pueden vaciar
    enviando `null`."""
    goal = _get_owned_goal(db, goal_id, current_user)
    if payload.name is not None:
        goal.name = payload.name
    if payload.target_amount is not None:
        goal.target_amount = payload.target_amount
    if payload.target_date is not None:
        goal.target_date = payload.target_date
    if payload.linked_account_id is not None:
        account = (
            db.query(Account)
            .filter(Account.id == payload.linked_account_id, Account.owner_id == current_user.id)
            .first()
        )
        if account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada"
            )
        goal.linked_account_id = payload.linked_account_id
    if payload.status is not None:
        goal.status = payload.status
    db.commit()
    db.refresh(goal)
    return _to_read(db, goal)


@router.delete(
    "/{goal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Borrar meta",
    responses=_GOAL_NOT_FOUND,
)
def delete_goal(
    goal_id: GoalId,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Borra la meta y sus aportaciones de forma definitiva."""
    goal = _get_owned_goal(db, goal_id, current_user)
    db.delete(goal)
    db.commit()


@router.post(
    "/{goal_id}/contributions",
    response_model=ContributionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una aportación",
    responses=_GOAL_NOT_FOUND,
)
def add_contribution(
    goal_id: GoalId,
    payload: ContributionCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ContributionRead:
    """Suma una aportación a la meta. No crea ningún movimiento en las
    cuentas. Al llegar al 80% crea la notificación `goal_near`, y al 100%
    `goal_reached` y la meta activa pasa a `completed`."""
    goal = _get_owned_goal(db, goal_id, current_user)

    contribution = GoalContribution(
        goal_id=goal.id,
        amount=payload.amount,
        contributed_at=payload.contributed_at,
        note=payload.note,
    )
    db.add(contribution)
    db.flush()

    check_goal_notifications(db, current_user, goal)

    if goal.status == "active" and _current_amount(db, goal.id) >= goal.target_amount:
        goal.status = "completed"

    db.commit()
    db.refresh(contribution)
    return ContributionRead(
        id=contribution.id,
        goal_id=contribution.goal_id,
        amount=contribution.amount,
        contributed_at=contribution.contributed_at,
        note=contribution.note,
        created_at=contribution.created_at,
    )


@router.get(
    "/{goal_id}/contributions",
    response_model=list[ContributionRead],
    summary="Listar las aportaciones de una meta",
    responses=_GOAL_NOT_FOUND,
)
def list_contributions(
    goal_id: GoalId,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[ContributionRead]:
    """Aportaciones de la meta, de la más reciente a la más antigua."""
    goal = _get_owned_goal(db, goal_id, current_user)
    contributions = (
        db.query(GoalContribution)
        .filter(GoalContribution.goal_id == goal.id)
        .order_by(GoalContribution.contributed_at.desc(), GoalContribution.id.desc())
        .all()
    )
    return [
        ContributionRead(
            id=c.id,
            goal_id=c.goal_id,
            amount=c.amount,
            contributed_at=c.contributed_at,
            note=c.note,
            created_at=c.created_at,
        )
        for c in contributions
    ]


@router.delete(
    "/{goal_id}/contributions/{contribution_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Borrar una aportación",
    responses=error_responses(
        404,
        e404=(
            "La meta o la aportación no existe, o es de otro usuario.",
            "Aportación no encontrada",
        ),
    ),
)
def delete_contribution(
    goal_id: GoalId,
    contribution_id: Annotated[int, Path(description="Id de la aportación.", examples=[31])],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Borra una aportación. Si la meta ya estaba `completed`, sigue así
    aunque baje del objetivo."""
    goal = _get_owned_goal(db, goal_id, current_user)
    contribution = (
        db.query(GoalContribution)
        .filter(GoalContribution.id == contribution_id, GoalContribution.goal_id == goal.id)
        .first()
    )
    if contribution is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Aportación no encontrada"
        )
    db.delete(contribution)
    db.commit()


@router.get(
    "/{goal_id}/projection",
    response_model=GoalProjection,
    summary="Proyectar cuándo se alcanzará la meta",
    responses=_GOAL_NOT_FOUND,
)
def get_projection(
    goal_id: GoalId,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> GoalProjection:
    """Estima la fecha al ritmo actual: media mensual aportada en los 3 meses
    naturales completos anteriores al actual (solo los posteriores a la
    creación de la meta; los meses sin aportación cuentan como 0).

    - Ya alcanzada: 0 meses restantes y la fecha de hoy.
    - Sin ningún mes completo desde la creación, o con ritmo 0:
      `has_enough_data: false` y sin fecha."""
    goal = _get_owned_goal(db, goal_id, current_user)
    today = date.today()
    current = _current_amount(db, goal.id)

    if current >= goal.target_amount:
        return GoalProjection(
            has_enough_data=True,
            monthly_pace=Decimal("0"),
            months_remaining=0,
            projected_date=today,
        )

    created_at_utc = goal.created_at.astimezone(UTC)
    created_month_start = _month_start(created_at_utc.year, created_at_utc.month)
    window = [
        (start, end)
        for start, end in _full_months_before(today, PROJECTION_WINDOW_MONTHS)
        if start >= created_month_start
    ]
    if not window:
        return GoalProjection(
            has_enough_data=False,
            monthly_pace=Decimal("0"),
            months_remaining=None,
            projected_date=None,
        )

    window_start = window[0][0]
    window_end = window[-1][1]
    total_in_window = (
        db.query(func.coalesce(func.sum(GoalContribution.amount), 0))
        .filter(
            GoalContribution.goal_id == goal.id,
            GoalContribution.contributed_at >= window_start,
            GoalContribution.contributed_at < window_end,
        )
        .scalar()
    ) or Decimal("0")

    monthly_pace = (total_in_window / len(window)).quantize(Decimal("0.01"))
    if monthly_pace <= 0:
        return GoalProjection(
            has_enough_data=False,
            monthly_pace=monthly_pace,
            months_remaining=None,
            projected_date=None,
        )

    remaining = goal.target_amount - current
    months_needed = math.ceil(remaining / monthly_pace)
    return GoalProjection(
        has_enough_data=True,
        monthly_pace=monthly_pace,
        months_remaining=months_needed,
        projected_date=_add_months(today, months_needed),
    )
