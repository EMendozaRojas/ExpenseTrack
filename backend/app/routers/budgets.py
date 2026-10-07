from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.core.openapi import AUTH_RESPONSES, Tag, error_responses
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

router = APIRouter(prefix="/budgets", tags=[Tag.PRESUPUESTOS], responses=AUTH_RESPONSES)

MONTH_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"
PeriodParam = Annotated[
    str, Path(pattern=MONTH_PATTERN, description="Mes en formato `YYYY-MM`.", examples=["2026-10"])
]
CategoryIdParam = Annotated[
    int, Path(description="Categoría de gasto del presupuesto.", examples=[95])
]
YearQuery = Annotated[int, Query(ge=2000, le=2100, description="Año.", examples=[2026])]
MonthQuery = Annotated[int, Query(ge=1, le=12, description="Mes (1–12).", examples=[10])]

_CATEGORY_NOT_FOUND = "La categoría no existe, no es de gasto o no es visible para el usuario."
_PAST_MONTH = "el mes es anterior al mes en curso (los meses pasados son de solo lectura)"


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


@router.get("/", response_model=list[BudgetStatus], summary="Listar los presupuestos de un mes")
def list_budgets(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    year: YearQuery,
    month: MonthQuery,
) -> list[BudgetStatus]:
    """Un elemento por categoría con presupuesto en ese mes, con el monto de
    ese mes, lo gastado, el porcentaje, el estado y, en el mes en curso, el
    ritmo de gasto.

    El presupuesto de cada mes se resuelve así: un monto propio de ese mes
    (o un mes saltado) gana sobre la serie que se repite. Lo gastado se
    calcula siempre con los movimientos actuales (para una categoría raíz,
    incluye sus subcategorías), salvo en meses conservados de una categoría
    borrada. Cada mes empieza en 0: no hay acumulación entre meses."""
    return [_to_status(e) for e in calc.evaluate_month(db, current_user.id, date(year, month, 1))]


@router.post(
    "/",
    response_model=BudgetStatus,
    status_code=status.HTTP_201_CREATED,
    summary="Crear presupuesto",
    responses=error_responses(
        404,
        409,
        e404=_CATEGORY_NOT_FOUND,
        e409=(
            f"La categoría ya tiene presupuesto en ese mes, o {_PAST_MONTH}.",
            "Ya existe un presupuesto para esta categoría en este mes",
        ),
    ),
)
def create_budget(
    payload: BudgetCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> BudgetStatus:
    """Crea el presupuesto de una categoría de gasto en el mes en curso o en
    uno futuro.

    - `repeat: true` (por defecto): el monto se repite en los meses
      siguientes hasta que se cambie o se borre (sin pisar una serie
      planificada más adelante).
    - `repeat: false`: solo ese mes.

    Puede haber presupuesto en una categoría raíz y en una de sus hijas a la
    vez; cada uno se evalúa por separado. Después revisa los avisos del mes
    en curso. Devuelve el presupuesto resuelto de ese mes."""
    category = _visible_expense_category(db, payload.category_id, current_user)
    month = date(payload.year, payload.month, 1)
    try:
        ops.create(db, current_user.id, category, month, payload.amount, payload.repeat)
    except ops.BudgetError as error:
        _raise_http(error)
    check_budget_notifications(db, current_user)
    return _status_for(db, current_user.id, category.id, month)


@router.get(
    "/recommendations",
    response_model=list[BudgetRecommendation],
    summary="Recomendar topes a partir del historial",
)
def list_recommendations(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    category_id: Annotated[
        int | None,
        Query(description="Solo la recomendación de esta categoría.", examples=[95]),
    ] = None,
) -> list[BudgetRecommendation]:
    """Para cada categoría de gasto con gasto en al menos 2 de los 3 meses
    naturales completos anteriores al actual, sugiere la media (redondeada)
    de los meses con gasto y la compara con su presupuesto del mes en curso:

    - `keep`: la sugerencia está a ±10% del monto actual;
    - `raise` / `lower`: hay que subirlo o bajarlo;
    - `create`: no tiene presupuesto y hubo gasto los 3 meses.

    El gasto del mismo mes del año anterior, `share_pct` y `over_typical`
    son informativos: no cambian la sugerencia ni la marca."""
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


@router.get(
    "/copy-preview",
    response_model=list[CopyPreviewItem],
    summary="Ver qué se puede copiar del mes anterior",
)
def copy_preview(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    year: YearQuery,
    month: MonthQuery,
) -> list[CopyPreviewItem]:
    """Presupuestos de un solo mes (que no se repiten) del mes anterior cuya
    categoría aún no tiene presupuesto en el mes indicado. Los que se
    repiten no aparecen porque ya se heredan. En meses pasados devuelve una
    lista vacía."""
    target = date(year, month, 1)
    if target < calc.current_month():
        return []
    return [
        CopyPreviewItem(category_id=b.category_id, category_name=b.category_name, amount=b.amount)
        for b in ops.copy_preview(db, current_user.id, target)
        if b.category_id is not None
    ]


@router.post(
    "/copy",
    response_model=CopyResult,
    summary="Copiar presupuestos del mes anterior",
    responses=error_responses(
        404,
        409,
        e404=_CATEGORY_NOT_FOUND,
        e409=(f"No se puede copiar: {_PAST_MONTH}.", "Los meses pasados son de solo lectura"),
    ),
)
def copy_budgets(
    payload: CopyRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CopyResult:
    """Crea presupuestos de un solo mes en el mes indicado, con los montos
    enviados (normalmente, los de `copy-preview` ajustados). Nunca pisa un
    presupuesto existente: esas categorías se omiten y se devuelven en
    `skipped`. Después revisa los avisos del mes en curso."""
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


@router.get(
    "/{category_id}/planned",
    response_model=list[PlannedMonthRead],
    summary="Ver los meses planificados de una categoría",
    responses=error_responses(404, e404=_CATEGORY_NOT_FOUND),
)
def planned_months(
    category_id: CategoryIdParam,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    from_: Annotated[
        str,
        Query(
            alias="from",
            pattern=MONTH_PATTERN,
            description="Mes `YYYY-MM` a partir del cual buscar (excluido).",
            examples=["2026-11"],
        ),
    ],
) -> list[PlannedMonthRead]:
    """Meses posteriores a `from` con un monto propio (un mes suelto, un
    monto distinto dentro de la serie o el inicio de otra serie). Sirve para
    avisar antes de confirmar "este mes y los siguientes": al editar se
    conservan, al borrar se borran."""
    _visible_expense_category(db, category_id, current_user)
    return [
        PlannedMonthRead(month=calc.month_key(p.month), amount=p.amount, kind=p.kind)
        for p in ops.planned_after(db, current_user.id, category_id, calc.parse_month_key(from_))
    ]


@router.put(
    "/{category_id}/{period}",
    response_model=BudgetStatus,
    summary="Editar el presupuesto de un mes",
    responses=error_responses(
        404,
        409,
        e404=f"La categoría no tiene presupuesto en ese mes. {_CATEGORY_NOT_FOUND}",
        e409=(f"No se puede editar: {_PAST_MONTH}.", "Los meses pasados son de solo lectura"),
    ),
)
def update_budget(
    category_id: CategoryIdParam,
    period: PeriodParam,
    payload: BudgetUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> BudgetStatus:
    """Cambia el monto del presupuesto de ese mes (actual o futuro). Si se
    repite, `scope` decide a qué meses afecta:

    - `this`: solo ese mes;
    - `following`: ese mes y los siguientes. Los meses posteriores con un
      monto propio se conservan.

    Con `repeat: false` deja de repetirse después de ese mes (que se
    conserva); con `repeat: true` un presupuesto de un solo mes empieza a
    repetirse. Los meses anteriores nunca cambian. Después revisa los avisos
    del mes en curso."""
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


@router.delete(
    "/{category_id}/{period}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Borrar el presupuesto de un mes",
    responses=error_responses(
        404,
        409,
        e404=f"La categoría no tiene presupuesto en ese mes. {_CATEGORY_NOT_FOUND}",
        e409=(f"No se puede borrar: {_PAST_MONTH}.", "Los meses pasados son de solo lectura"),
    ),
)
def delete_budget(
    category_id: CategoryIdParam,
    period: PeriodParam,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    scope: Annotated[
        Scope,
        Query(
            description="Si el presupuesto se repite: `this` (solo ese mes) o `following` "
            "(ese mes y los siguientes, incluidos los meses planificados).",
            examples=["this"],
        ),
    ] = "this",
) -> None:
    """Borra el presupuesto de ese mes (actual o futuro). Los meses
    anteriores conservan su historial."""
    category = _visible_expense_category(db, category_id, current_user)
    try:
        ops.delete(db, current_user.id, category, calc.parse_month_key(period), scope)
    except ops.BudgetError as error:
        _raise_http(error)
    check_budget_notifications(db, current_user)
