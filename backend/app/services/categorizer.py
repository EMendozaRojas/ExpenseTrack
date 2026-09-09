import re
import unicodedata
from collections.abc import Iterable

from sqlalchemy.orm import Session

from app.db.seed_categories import UNCATEGORIZED_EXPENSE, UNCATEGORIZED_INCOME
from app.models.categorization_rule import CategorizationRule
from app.models.category import Category

_CARD_NUMBER_RE = re.compile(r"\d{4,}")
_WHITESPACE_RE = re.compile(r"\s+")

_PREFIXES = (
    "COMPRA EN",
    "PAGO EN",
    "PAGO",
    "RECIBO",
    "ADEUDO",
    "BIZUM DE",
    "BIZUM A",
    "TRANSFERENCIA DE",
    "TRANSFERENCIA A",
    "TRANSFERENCIA",
)


def normalize(text: str | None) -> str:
    """Normaliza una descripción de movimiento para hacer match con reglas.

    Mayúsculas, sin acentos, sin números de tarjeta/cuenta, sin prefijos
    bancarios comunes, espacios colapsados.
    """
    if not text:
        return ""

    upper = text.upper()
    without_accents = "".join(
        char for char in unicodedata.normalize("NFKD", upper) if not unicodedata.combining(char)
    )
    without_numbers = _CARD_NUMBER_RE.sub("", without_accents)
    collapsed = _WHITESPACE_RE.sub(" ", without_numbers).strip()

    for prefix in _PREFIXES:
        if collapsed.startswith(prefix):
            collapsed = collapsed[len(prefix) :].strip()
            break

    return collapsed


def _rule_matches(normalized_description: str, rule: CategorizationRule) -> bool:
    normalized_pattern = normalize(rule.pattern)
    if not normalized_pattern:
        return False
    if rule.match_type == "starts_with":
        return normalized_description.startswith(normalized_pattern)
    return normalized_pattern in normalized_description


def _sort_key(rule: CategorizationRule) -> tuple[int, int]:
    return (-rule.priority, rule.id)


def match_category(
    raw_description: str | None, rules: Iterable[CategorizationRule]
) -> int | None:
    """Devuelve el category_id de la primera regla habilitada que hace match.

    Las reglas del usuario (owner_id no nulo) se evalúan antes que las del
    sistema, cada grupo ordenado por prioridad descendente y luego por id.
    """
    normalized_description = normalize(raw_description)
    if not normalized_description:
        return None

    enabled_rules = [rule for rule in rules if rule.is_enabled]
    user_rules = sorted((r for r in enabled_rules if r.owner_id is not None), key=_sort_key)
    system_rules = sorted((r for r in enabled_rules if r.owner_id is None), key=_sort_key)

    for rule in (*user_rules, *system_rules):
        if _rule_matches(normalized_description, rule):
            return rule.category_id
    return None


def uncategorized_category_id(db: Session, kind: str = "expense") -> int:
    """Id de la subcategoría de sistema 'Sin Clasificar' para ese `kind`.

    Toda transacción de income/expense debe apuntar a una subcategoría real
    (regla de negocio confirmada en producto); esta es el destino por
    defecto cuando ninguna regla de categorización aplica.
    """
    root_name, sub_name = UNCATEGORIZED_EXPENSE if kind == "expense" else UNCATEGORIZED_INCOME
    root = (
        db.query(Category)
        .filter(
            Category.name == root_name,
            Category.parent_id.is_(None),
            Category.is_system.is_(True),
        )
        .first()
    )
    category = (
        db.query(Category)
        .filter(
            Category.name == sub_name,
            Category.parent_id == root.id,
            Category.is_system.is_(True),
        )
        .first()
        if root is not None
        else None
    )
    if category is None:
        raise RuntimeError(
            "Categoría 'Sin Clasificar' no encontrada; falta aplicar la migración de seed"
        )
    return category.id
