"""Detección de duplicados al importar un extracto.

Regla de negocio: `external_hash` (cuenta + fecha + importe + descripción
normalizada) es la red de seguridad exacta; el match difuso (mismo importe,
fecha ±1 día, texto similar ≥85%) cubre el caso en que el banco cambia
ligeramente el formato del texto entre extractos.
"""

import hashlib
from datetime import date
from decimal import Decimal
from difflib import SequenceMatcher

from app.models.transaction import Transaction

PROBABLE_MATCH_THRESHOLD = 0.85
PROBABLE_MATCH_DAY_TOLERANCE = 1


def external_hash(account_id: int, posted_at: date, amount: Decimal, description: str) -> str:
    normalized_description = " ".join(description.upper().split())
    raw = (
        f"{account_id}|{posted_at.isoformat()}|{amount.quantize(Decimal('0.01'))}|"
        f"{normalized_description}"
    )
    return hashlib.sha256(raw.encode()).hexdigest()


def _text_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.upper(), b.upper()).ratio()


def find_probable_duplicate(
    posted_at: date, amount: Decimal, description: str, candidates: list[Transaction]
) -> Transaction | None:
    for tx in candidates:
        if tx.amount != amount:
            continue
        if abs((tx.posted_at - posted_at).days) > PROBABLE_MATCH_DAY_TOLERANCE:
            continue
        candidate_text = tx.raw_description or tx.note or ""
        if _text_similarity(candidate_text, description) >= PROBABLE_MATCH_THRESHOLD:
            return tx
    return None
