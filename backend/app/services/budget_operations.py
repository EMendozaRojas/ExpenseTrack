"""Operaciones de escritura sobre presupuestos mensuales (design D2, D7, D8).

Mantiene dos invariantes:
- las series de una misma categoría nunca se solapan;
- los meses anteriores al mes en curso no se modifican (solo lectura),
  salvo al congelar el historial de una categoría que se borra.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.budget import Budget
from app.models.budget_month import BudgetMonth
from app.models.category import Category
from app.services import budget_calculator as calc

SCOPE_THIS = "this"
SCOPE_FOLLOWING = "following"


class BudgetError(Exception):
    """Error de negocio; el router lo traduce a HTTP."""


class BudgetConflict(BudgetError):
    pass


class BudgetNotFound(BudgetError):
    pass


@dataclass
class PlannedMonth:
    month: date
    amount: Decimal
    kind: str  # "override" | "single" | "series"


def _ensure_not_past(month: date) -> None:
    if month < calc.current_month():
        raise BudgetConflict("Los meses pasados son de solo lectura")


def _entry(db: Session, owner_id: int, category_id: int, month: date) -> BudgetMonth | None:
    return (
        db.query(BudgetMonth)
        .filter(
            BudgetMonth.owner_id == owner_id,
            BudgetMonth.category_id == category_id,
            BudgetMonth.month == month,
        )
        .first()
    )


def _category_series(db: Session, owner_id: int, category_id: int) -> list[Budget]:
    return (
        db.query(Budget)
        .filter(Budget.owner_id == owner_id, Budget.category_id == category_id)
        .order_by(Budget.starts_on)
        .all()
    )


def _covering_series(db: Session, owner_id: int, category_id: int, month: date) -> Budget | None:
    return next(
        (s for s in _category_series(db, owner_id, category_id) if calc.series_covers(s, month)),
        None,
    )


def _next_series_start(db: Session, owner_id: int, category_id: int, month: date) -> date | None:
    later = [
        s.starts_on for s in _category_series(db, owner_id, category_id) if s.starts_on > month
    ]
    return min(later) if later else None


def _upsert_entry(
    db: Session, owner_id: int, category: Category, month: date, kind: str, amount: Decimal | None
) -> BudgetMonth:
    entry = _entry(db, owner_id, category.id, month)
    if entry is None:
        entry = BudgetMonth(
            owner_id=owner_id, category_id=category.id, category_name=category.name, month=month
        )
        db.add(entry)
    entry.kind = kind
    entry.amount = amount
    entry.category_name = category.name
    return entry


def _normalize_entries(db: Session, owner_id: int, category_id: int) -> None:
    """Tras acortar o borrar series: los `skip` fuera de toda serie sobran y
    los `override` fuera de toda serie pasan a ser meses sueltos (se conservan
    los meses planificados a mano)."""
    db.flush()
    series = _category_series(db, owner_id, category_id)
    entries = (
        db.query(BudgetMonth)
        .filter(BudgetMonth.owner_id == owner_id, BudgetMonth.category_id == category_id)
        .all()
    )
    for entry in entries:
        covered = any(calc.series_covers(s, entry.month) for s in series)
        if covered and entry.kind == "single":
            entry.kind = "override"
        elif not covered and entry.kind == "skip":
            db.delete(entry)
        elif not covered and entry.kind == "override":
            entry.kind = "single"


def _start_series(
    db: Session, owner_id: int, category: Category, month: date, amount: Decimal
) -> Budget:
    series = Budget(
        owner_id=owner_id,
        category_id=category.id,
        category_name=category.name,
        amount=amount,
        starts_on=month,
        # No pisa una serie planificada más adelante.
        ends_on=_next_series_start(db, owner_id, category.id, month),
    )
    db.add(series)
    return series


def create(
    db: Session, owner_id: int, category: Category, month: date, amount: Decimal, repeat: bool
) -> None:
    _ensure_not_past(month)
    if calc.resolve_one(db, owner_id, category.id, month) is not None:
        raise BudgetConflict("Ya existe un presupuesto para esta categoría en este mes")

    covering = _covering_series(db, owner_id, category.id, month)
    if covering is not None:
        # El mes estaba saltado dentro de una serie: se quita el salto.
        skipped = _entry(db, owner_id, category.id, month)
        if skipped is not None:
            db.delete(skipped)
            db.flush()
        if repeat:
            _apply_following(db, owner_id, category, covering, month, amount)
        elif amount != covering.amount:
            _upsert_entry(db, owner_id, category, month, "override", amount)
    elif repeat:
        _start_series(db, owner_id, category, month, amount)
    else:
        _upsert_entry(db, owner_id, category, month, "single", amount)
    _normalize_entries(db, owner_id, category.id)
    db.commit()


def _apply_following(
    db: Session,
    owner_id: int,
    category: Category,
    series: Budget,
    month: date,
    amount: Decimal,
    extend: bool = False,
) -> None:
    """Desde `month` en adelante el monto pasa a ser `amount`, hasta donde
    terminaba la serie o, con `extend`, hasta la siguiente serie planificada."""
    end = (
        _next_series_start(db, owner_id, category.id, series.starts_on)
        if extend
        else series.ends_on
    )
    if series.starts_on == month:
        series.amount = amount
        series.ends_on = end
    else:
        series.ends_on = month
        db.add(
            Budget(
                owner_id=owner_id,
                category_id=category.id,
                category_name=category.name,
                amount=amount,
                starts_on=month,
                ends_on=end,
            )
        )
    override = _entry(db, owner_id, category.id, month)
    if override is not None and override.kind == "override":
        db.delete(override)


def update(
    db: Session,
    owner_id: int,
    category: Category,
    month: date,
    amount: Decimal,
    scope: str,
    repeat: bool | None,
) -> None:
    _ensure_not_past(month)
    resolved = calc.resolve_one(db, owner_id, category.id, month)
    if resolved is None:
        raise BudgetNotFound("Presupuesto no encontrado")

    series = resolved.series
    if series is None:
        entry = resolved.entry
        assert entry is not None
        if repeat:
            db.delete(entry)
            db.flush()
            _start_series(db, owner_id, category, month, amount)
        else:
            entry.amount = amount
    elif repeat is False:
        # Deja de repetirse después de este mes; este mes se conserva.
        next_month = calc.add_months(month, 1)
        if series.ends_on is None or series.ends_on > next_month:
            series.ends_on = next_month
        if amount != series.amount:
            _upsert_entry(db, owner_id, category, month, "override", amount)
    elif repeat is True and series.ends_on is not None:
        # Vuelve a repetirse una serie que tenía fin.
        _apply_following(db, owner_id, category, series, month, amount, extend=True)
    elif scope == SCOPE_FOLLOWING:
        _apply_following(db, owner_id, category, series, month, amount)
    elif amount == series.amount:
        if resolved.entry is not None:
            db.delete(resolved.entry)
    else:
        _upsert_entry(db, owner_id, category, month, "override", amount)
    _normalize_entries(db, owner_id, category.id)
    db.commit()


def delete(db: Session, owner_id: int, category: Category, month: date, scope: str) -> None:
    _ensure_not_past(month)
    resolved = calc.resolve_one(db, owner_id, category.id, month)
    if resolved is None:
        raise BudgetNotFound("Presupuesto no encontrado")

    series = resolved.series
    if series is None:
        assert resolved.entry is not None
        db.delete(resolved.entry)
    elif scope == SCOPE_THIS:
        _upsert_entry(db, owner_id, category, month, "skip", None)
    else:
        for other in _category_series(db, owner_id, category.id):
            if other.starts_on >= month:
                db.delete(other)
        if series.starts_on < month:
            series.ends_on = month
        for entry in (
            db.query(BudgetMonth)
            .filter(
                BudgetMonth.owner_id == owner_id,
                BudgetMonth.category_id == category.id,
                BudgetMonth.month >= month,
            )
            .all()
        ):
            db.delete(entry)
    _normalize_entries(db, owner_id, category.id)
    db.commit()


def planned_after(db: Session, owner_id: int, category_id: int, month: date) -> list[PlannedMonth]:
    """Meses posteriores a `month` con un monto propio: los que la UI menciona
    al confirmar "Este mes y los siguientes"."""
    planned = [
        PlannedMonth(month=e.month, amount=e.amount, kind=e.kind)
        for e in db.query(BudgetMonth)
        .filter(
            BudgetMonth.owner_id == owner_id,
            BudgetMonth.category_id == category_id,
            BudgetMonth.month > month,
            BudgetMonth.kind.in_(("override", "single")),
        )
        .all()
        if e.amount is not None
    ]
    planned += [
        PlannedMonth(month=s.starts_on, amount=s.amount, kind="series")
        for s in _category_series(db, owner_id, category_id)
        if s.starts_on > month
    ]
    return sorted(planned, key=lambda p: p.month)


def copy_preview(db: Session, owner_id: int, month: date) -> list[calc.ResolvedBudget]:
    existing = {b.category_id for b in calc.resolve_month(db, owner_id, month)}
    previous = calc.resolve_month(db, owner_id, calc.add_months(month, -1))
    return [
        b
        for b in previous
        if b.source == "single" and b.category_id is not None and b.category_id not in existing
    ]


def copy(
    db: Session, owner_id: int, month: date, items: list[tuple[Category, Decimal]]
) -> tuple[list[int], list[int]]:
    """Crea presupuestos de un solo mes; devuelve (creados, omitidos)."""
    _ensure_not_past(month)
    created: list[int] = []
    skipped: list[int] = []
    for category, amount in items:
        try:
            create(db, owner_id, category, month, amount, repeat=False)
            created.append(category.id)
        except BudgetConflict:
            skipped.append(category.id)
    return created, skipped


def freeze_for_category(db: Session, owner_id: int, category: Category) -> bool:
    """Antes de borrar una categoría: conserva sus meses pasados con el monto y
    lo gastado en ese momento, y quita sus presupuestos desde el mes en curso.
    Devuelve si la categoría tenía presupuestos."""
    series = _category_series(db, owner_id, category.id)
    entries = (
        db.query(BudgetMonth)
        .filter(BudgetMonth.owner_id == owner_id, BudgetMonth.category_id == category.id)
        .all()
    )
    if not series and not entries:
        return False

    current = calc.current_month()
    first = min([s.starts_on for s in series] + [e.month for e in entries])
    month = first
    while month < current:
        resolved = calc.resolve_one(db, owner_id, category.id, month)
        if resolved is not None:
            evaluation = calc.evaluate(db, owner_id, [resolved], month)[0]
            entry = _upsert_entry(db, owner_id, category, month, "single", resolved.amount)
            entry.frozen_spent = evaluation.spent
        else:
            skipped = _entry(db, owner_id, category.id, month)
            if skipped is not None:
                db.delete(skipped)
        month = calc.add_months(month, 1)
        db.flush()

    for s in series:
        db.delete(s)
    for entry in entries:
        if entry.month >= current:
            db.delete(entry)
    db.flush()
    return True
