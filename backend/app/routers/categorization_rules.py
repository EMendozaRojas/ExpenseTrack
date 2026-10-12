from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.core.openapi import AUTH_RESPONSES, Tag, error_responses
from app.models.categorization_rule import MATCH_TYPES, CategorizationRule
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.categorization_rule import (
    CategorizationRuleCreate,
    CategorizationRuleRead,
    CategorizationRuleUpdate,
    RuleApplyResult,
    RulePreviewResult,
)
from app.services.categorizer import normalize, uncategorized_category_id

router = APIRouter(prefix="/categorization-rules", tags=[Tag.REGLAS], responses=AUTH_RESPONSES)

RuleId = Annotated[int, Path(description="Id de la regla.", examples=[12])]
_RULE_NOT_FOUND = ("La regla no existe o es de otro usuario.", "Regla no encontrada")
_MATCH_TYPE_INVALID = ("`match_type` no es `contains` ni `starts_with`.", "match_type no soportado")


def _match_text(transaction: Transaction) -> str:
    parts = [transaction.counterparty, transaction.raw_description, transaction.note]
    return " ".join(part for part in parts if part)


def _matches(normalized_description: str, match_type: str, pattern: str) -> bool:
    normalized_pattern = normalize(pattern)
    if not normalized_pattern:
        return False
    if match_type == "starts_with":
        return normalized_description.startswith(normalized_pattern)
    return normalized_pattern in normalized_description


def _check_category_visible(db: Session, category_id: int, current_user: User) -> None:
    category = (
        db.query(Category)
        .filter(
            Category.id == category_id,
            or_(Category.owner_id.is_(None), Category.owner_id == current_user.id),
        )
        .first()
    )
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")


def _get_owned_rule(db: Session, rule_id: int, current_user: User) -> CategorizationRule:
    rule = (
        db.query(CategorizationRule)
        .filter(CategorizationRule.id == rule_id, CategorizationRule.owner_id == current_user.id)
        .first()
    )
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regla no encontrada")
    return rule


@router.get("/", response_model=list[CategorizationRuleRead], summary="Listar reglas")
def list_rules(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[CategorizationRule]:
    """Reglas propias del usuario, de mayor a menor prioridad. Las reglas de
    sistema no se listan, aunque también se aplican."""
    return (
        db.query(CategorizationRule)
        .filter(CategorizationRule.owner_id == current_user.id)
        .order_by(CategorizationRule.priority.desc(), CategorizationRule.id)
        .all()
    )


@router.post(
    "/",
    response_model=CategorizationRuleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear regla",
    responses=error_responses(
        404,
        422,
        e404=("La categoría no existe o no es visible.", "Categoría no encontrada"),
        e422=_MATCH_TYPE_INVALID,
    ),
)
def create_rule(
    payload: CategorizationRuleCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CategorizationRule:
    """Crea una regla que asigna `category_id` a los movimientos nuevos cuya
    descripción contiene (o empieza por) `pattern`.

    La comparación ignora mayúsculas, acentos, números de tarjeta y prefijos
    bancarios. Las reglas del usuario se evalúan antes que las de sistema,
    cada grupo por prioridad descendente. No recategoriza movimientos
    existentes: para eso, `POST /categorization-rules/{rule_id}/apply`."""
    if payload.match_type not in MATCH_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="match_type no soportado"
        )
    _check_category_visible(db, payload.category_id, current_user)

    rule = CategorizationRule(
        owner_id=current_user.id,
        match_type=payload.match_type,
        pattern=payload.pattern,
        category_id=payload.category_id,
        priority=payload.priority,
        is_enabled=payload.is_enabled,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.patch(
    "/{rule_id}",
    response_model=CategorizationRuleRead,
    summary="Editar regla",
    responses=error_responses(
        404,
        422,
        e404="La regla, o la categoría indicada, no existe o es de otro usuario.",
        e422=_MATCH_TYPE_INVALID,
    ),
)
def update_rule(
    rule_id: RuleId,
    payload: CategorizationRuleUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CategorizationRule:
    """Cambia los campos enviados de una regla propia; el resto no cambia."""
    rule = _get_owned_rule(db, rule_id, current_user)
    if payload.match_type is not None:
        if payload.match_type not in MATCH_TYPES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="match_type no soportado"
            )
        rule.match_type = payload.match_type
    if payload.pattern is not None:
        rule.pattern = payload.pattern
    if payload.category_id is not None:
        _check_category_visible(db, payload.category_id, current_user)
        rule.category_id = payload.category_id
    if payload.priority is not None:
        rule.priority = payload.priority
    if payload.is_enabled is not None:
        rule.is_enabled = payload.is_enabled
    db.commit()
    db.refresh(rule)
    return rule


@router.delete(
    "/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Borrar regla",
    responses=error_responses(404, e404=_RULE_NOT_FOUND),
)
def delete_rule(
    rule_id: RuleId,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Borra una regla propia. Los movimientos ya categorizados no cambian."""
    rule = _get_owned_rule(db, rule_id, current_user)
    db.delete(rule)
    db.commit()


@router.get(
    "/preview",
    response_model=RulePreviewResult,
    summary="Probar un patrón",
    responses=error_responses(422, e422=_MATCH_TYPE_INVALID),
)
def preview_rule(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    pattern: Annotated[str, Query(description="Texto a buscar.", examples=["mercadona"])],
    match_type: Annotated[
        str, Query(description="`contains` o `starts_with`.", examples=["contains"])
    ] = "contains",
) -> RulePreviewResult:
    """Cuenta cuántos movimientos no borrados del usuario (de cualquier
    categoría) coincidirían con el patrón, sin crear la regla."""
    if match_type not in MATCH_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="match_type no soportado"
        )
    transactions = (
        db.query(Transaction)
        .filter(Transaction.owner_id == current_user.id, Transaction.deleted_at.is_(None))
        .all()
    )
    count = sum(
        1 for tx in transactions if _matches(normalize(_match_text(tx)), match_type, pattern)
    )
    return RulePreviewResult(matching_count=count)


@router.post(
    "/{rule_id}/apply",
    response_model=RuleApplyResult,
    summary="Aplicar una regla a los movimientos sin clasificar",
    responses=error_responses(
        404, e404=("La regla no existe o no es visible.", "Regla no encontrada")
    ),
)
def apply_rule(
    rule_id: RuleId,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> RuleApplyResult:
    """Aplica una regla (propia o de sistema) a los movimientos del usuario
    que están en "Sin Clasificar" y coinciden con ella. Los ya categorizados
    no se tocan."""
    rule = (
        db.query(CategorizationRule)
        .filter(
            CategorizationRule.id == rule_id,
            or_(
                CategorizationRule.owner_id.is_(None),
                CategorizationRule.owner_id == current_user.id,
            ),
        )
        .first()
    )
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regla no encontrada")

    uncategorized_ids = {
        uncategorized_category_id(db, "expense"),
        uncategorized_category_id(db, "income"),
    }
    candidates = (
        db.query(Transaction)
        .filter(
            Transaction.owner_id == current_user.id,
            Transaction.deleted_at.is_(None),
            Transaction.category_id.in_(uncategorized_ids),
        )
        .all()
    )
    updated = 0
    for tx in candidates:
        if _matches(normalize(_match_text(tx)), rule.match_type, rule.pattern):
            tx.category_id = rule.category_id
            updated += 1
    db.commit()
    return RuleApplyResult(updated_count=updated)
