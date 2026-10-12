"""Detección de series recurrentes (gasto o ingreso) bajo demanda.

Regla de negocio: se agrupa por contraparte/descripción normalizada (misma
`normalize()` que usan las reglas de categorización) + dirección; una serie
es "recurrente" con ≥3 ocurrencias, importe dentro de ±25% de la media del
grupo, y cadencia regular entre ocurrencias (coeficiente de variación de los
huecos en días ≤ 0.5). No se persiste la serie, solo se recalcula.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from statistics import mean, pstdev

from app.models.transaction import Transaction
from app.services.categorizer import normalize

MIN_OCCURRENCES = 3
AMOUNT_TOLERANCE_PCT = Decimal("0.25")
MAX_CADENCE_COEFFICIENT_OF_VARIATION = 0.5

_CADENCE_BANDS = (
    (5, 9, "semanal"),
    (12, 16, "quincenal"),
    (25, 35, "mensual"),
    (85, 95, "trimestral"),
)


@dataclass
class RecurringSeries:
    key: str
    label: str
    direction: str
    category_id: int | None
    category_name: str | None
    occurrences: int
    avg_amount: Decimal
    cadence_days: float
    cadence_label: str
    first_posted_at: date
    last_posted_at: date


def _cadence_label(mean_gap_days: float) -> str:
    for low, high, label in _CADENCE_BANDS:
        if low <= mean_gap_days <= high:
            return label
    return "irregular"


def detect_recurring_series(transactions: list[Transaction]) -> list[RecurringSeries]:
    groups: dict[tuple[str, str], list[Transaction]] = defaultdict(list)
    for tx in transactions:
        text = tx.counterparty or tx.raw_description or tx.note
        key_text = normalize(text)
        if not key_text:
            continue
        groups[(key_text, tx.direction)].append(tx)

    series: list[RecurringSeries] = []
    for (key_text, direction), txs in groups.items():
        if len(txs) < MIN_OCCURRENCES:
            continue

        txs_sorted = sorted(txs, key=lambda t: t.posted_at)
        amounts = [abs(t.amount) for t in txs_sorted]
        avg_amount = sum(amounts, Decimal(0)) / len(amounts)
        if avg_amount <= 0:
            continue
        if any(abs(a - avg_amount) / avg_amount > AMOUNT_TOLERANCE_PCT for a in amounts):
            continue

        gaps = [
            (txs_sorted[i].posted_at - txs_sorted[i - 1].posted_at).days
            for i in range(1, len(txs_sorted))
        ]
        if not gaps or any(g <= 0 for g in gaps):
            continue
        mean_gap = mean(gaps)
        coefficient_of_variation = (pstdev(gaps) / mean_gap) if mean_gap else 1.0
        if coefficient_of_variation > MAX_CADENCE_COEFFICIENT_OF_VARIATION:
            continue

        last = txs_sorted[-1]
        series.append(
            RecurringSeries(
                key=f"{direction}:{key_text}",
                label=last.counterparty or last.raw_description or last.note or key_text,
                direction=direction,
                category_id=last.category_id,
                category_name=last.category.name if last.category else None,
                occurrences=len(txs_sorted),
                avg_amount=avg_amount.quantize(Decimal("0.01")),
                cadence_days=round(mean_gap, 1),
                cadence_label=_cadence_label(mean_gap),
                first_posted_at=txs_sorted[0].posted_at,
                last_posted_at=last.posted_at,
            )
        )

    series.sort(key=lambda s: s.last_posted_at, reverse=True)
    return series
