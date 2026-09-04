from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
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
from app.services.categorizer import normalize

router = APIRouter(prefix="/categorization-rules", tags=["categorization-rules"])


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada"
        )


def _get_owned_rule(db: Session, rule_id: int, current_user: User) -> CategorizationRule:
    rule = (
        db.query(CategorizationRule)
        .filter(CategorizationRule.id == rule_id, CategorizationRule.owner_id == current_user.id)
        .first()
    )
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regla no encontrada")
    return rule


@router.get("/", response_model=list[CategorizationRuleRead])
def list_rules(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[CategorizationRule]:
    return (
        db.query(CategorizationRule)
        .filter(CategorizationRule.owner_id == current_user.id)
        .order_by(CategorizationRule.priority.desc(), CategorizationRule.id)
        .all()
    )


@router.post("/", response_model=CategorizationRuleRead, status_code=status.HTTP_201_CREATED)
def create_rule(
    payload: CategorizationRuleCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CategorizationRule:
    if payload.match_type not in MATCH_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="match_type no soportado"
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


@router.patch("/{rule_id}", response_model=CategorizationRuleRead)
def update_rule(
    rule_id: int,
    payload: CategorizationRuleUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CategorizationRule:
    rule = _get_owned_rule(db, rule_id, current_user)
    if payload.match_type is not None:
        if payload.match_type not in MATCH_TYPES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="match_type no soportado"
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


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(
    rule_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    rule = _get_owned_rule(db, rule_id, current_user)
    db.delete(rule)
    db.commit()


@router.get("/preview", response_model=RulePreviewResult)
def preview_rule(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    pattern: str,
    match_type: Annotated[str, Query()] = "contains",
) -> RulePreviewResult:
    if match_type not in MATCH_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="match_type no soportado"
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


@router.post("/{rule_id}/apply", response_model=RuleApplyResult)
def apply_rule(
    rule_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> RuleApplyResult:
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

    candidates = (
        db.query(Transaction)
        .filter(
            Transaction.owner_id == current_user.id,
            Transaction.deleted_at.is_(None),
            Transaction.category_id.is_(None),
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
