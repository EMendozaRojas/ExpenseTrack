"""Recomendaciones de tope mensual a partir del historial (design D10).

Ventana: los 3 meses naturales completos anteriores al mes en curso. Para
cada categoría de gasto con gasto en al menos 2 de esos meses se sugiere la
media (redondeada) de los meses con gasto, y se compara con su presupuesto
del mes en curso. El mismo mes del año anterior, `share_pct` y
`over_typical` son informativos: no cambian la sugerencia ni el flag.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.category import Category
from app.services import budget_calculator as calc

WINDOW_MONTHS = 3
MIN_MONTHS_WITH_SPEND = 2
KEEP_BAND = Decimal("0.10")
# Bandas de referencia (Apéndice C de budgets-and-savings-goals): % máximo
# típico del gasto total para estas categorías raíz de sistema.
TYPICAL_SHARE_PCT = {"Vivienda": 35, "Transporte": 20, "Alimentación": 15}


@dataclass
class Recommendation:
    category: Category
    flag: str  # "raise" | "lower" | "keep" | "create"
    suggested_amount: Decimal
    current_amount: Decimal | None
    monthly_spent: list[tuple[date, Decimal]]
    mean: Decimal
    same_month_last_year: Decimal | None
    share_pct: float | None = None
    over_typical: bool | None = field(default=None)


def recommend(db: Session, owner_id: int, category_id: int | None = None) -> list[Recommendation]:
    current = calc.current_month()
    window = [calc.add_months(current, -i) for i in range(WINDOW_MONTHS, 0, -1)]
    last_year = calc.add_months(current, -12)

    categories = (
        db.query(Category)
        .filter(
            Category.kind == "expense",
            or_(Category.owner_id.is_(None), Category.owner_id == owner_id),
        )
        .all()
    )
    if category_id is not None:
        categories = [c for c in categories if c.id == category_id]
    ids_by_category = calc.subtree_ids(db, categories)
    all_ids = sorted({cid for ids in ids_by_category.values() for cid in ids})
    spent_map = calc.spent_by_category_and_month(db, owner_id, all_ids, last_year, current)

    def spent(category: Category, month: date) -> Decimal:
        return sum(
            (spent_map.get((cid, month), Decimal("0")) for cid in ids_by_category[category.id]),
            Decimal("0"),
        )

    roots = [c for c in categories if c.parent_id is None]
    window_total = sum((spent(root, m) for root in roots for m in window), Decimal("0"))
    budgets = {b.category_id: b for b in calc.resolve_month(db, owner_id, current)}

    recommendations: list[Recommendation] = []
    for category in categories:
        monthly = [(m, spent(category, m)) for m in window]
        with_spend = [value for _, value in monthly if value > 0]
        if len(with_spend) < MIN_MONTHS_WITH_SPEND:
            continue
        mean = sum(with_spend, Decimal("0")) / len(with_spend)
        suggested = mean.quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        budget = budgets.get(category.id)
        if budget is None:
            if len(with_spend) < WINDOW_MONTHS:
                continue
            flag = "create"
        elif abs(suggested - budget.amount) <= budget.amount * KEEP_BAND:
            flag = "keep"
        else:
            flag = "raise" if suggested > budget.amount else "lower"

        last_year_spent = spent(category, last_year)
        recommendation = Recommendation(
            category=category,
            flag=flag,
            suggested_amount=suggested.quantize(Decimal("0.01")),
            current_amount=budget.amount if budget else None,
            monthly_spent=[(m, v.quantize(Decimal("0.01"))) for m, v in monthly],
            mean=mean.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            same_month_last_year=last_year_spent.quantize(Decimal("0.01"))
            if last_year_spent > 0
            else None,
        )
        if category.parent_id is None and category.is_system and window_total > 0:
            share = float(sum((v for _, v in monthly), Decimal("0")) / window_total * 100)
            recommendation.share_pct = round(share, 1)
            band = TYPICAL_SHARE_PCT.get(category.name)
            recommendation.over_typical = share > band if band is not None else None
        recommendations.append(recommendation)

    recommendations.sort(key=lambda r: r.category.name.lower())
    return recommendations
