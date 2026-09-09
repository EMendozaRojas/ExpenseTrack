import base64
import uuid
from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.account import Account
from app.models.categorization_rule import CategorizationRule
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.categorization_rule import BulkCategorizeRequest, BulkCategorizeResult
from app.schemas.transaction import (
    TransactionCreate,
    TransactionPage,
    TransactionRead,
    TransactionUpdate,
    TransferCreate,
)
from app.services.categorizer import match_category, uncategorized_category_id
from app.services.fx import MissingFxRateError, convert

router = APIRouter(prefix="/transactions", tags=["transactions"])


def _autocategorize(
    db: Session, current_user: User, counterparty: str | None, note: str | None
) -> int | None:
    rules = (
        db.query(CategorizationRule)
        .filter(
            or_(
                CategorizationRule.owner_id.is_(None),
                CategorizationRule.owner_id == current_user.id,
            ),
            CategorizationRule.is_enabled.is_(True),
        )
        .all()
    )
    text = counterparty or note
    return match_category(text, rules)

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200


def _encode_cursor(posted_at: date, transaction_id: int) -> str:
    raw = f"{posted_at.isoformat()}|{transaction_id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def _decode_cursor(cursor: str) -> tuple[date, int]:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        posted_at_str, id_str = raw.split("|")
        return date.fromisoformat(posted_at_str), int(id_str)
    except (ValueError, UnicodeDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cursor inválido"
        ) from exc


def _get_owned_account(db: Session, account_id: int, current_user: User) -> Account:
    account = (
        db.query(Account)
        .filter(Account.id == account_id, Account.owner_id == current_user.id)
        .first()
    )
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada")
    return account


def _check_category(db: Session, category_id: int | None, current_user: User) -> None:
    if category_id is None:
        return
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
    if category.parent_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Una transacción debe asignarse a una subcategoría, no a la categoría principal",
        )


def _get_owned_transaction(db: Session, transaction_id: int, current_user: User) -> Transaction:
    transaction = (
        db.query(Transaction)
        .filter(
            Transaction.id == transaction_id,
            Transaction.owner_id == current_user.id,
            Transaction.deleted_at.is_(None),
        )
        .first()
    )
    if transaction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gasto no encontrado")
    return transaction


@router.get("/", response_model=TransactionPage)
def list_transactions(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    account_id: int | None = None,
    category_id: int | None = None,
    direction: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    q: str | None = None,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    cursor: str | None = None,
) -> TransactionPage:
    query = db.query(Transaction).filter(
        Transaction.owner_id == current_user.id, Transaction.deleted_at.is_(None)
    )
    if account_id is not None:
        query = query.filter(Transaction.account_id == account_id)
    if category_id is not None:
        query = query.filter(Transaction.category_id == category_id)
    if direction is not None:
        query = query.filter(Transaction.direction == direction)
    if date_from is not None:
        query = query.filter(Transaction.posted_at >= date_from)
    if date_to is not None:
        query = query.filter(Transaction.posted_at <= date_to)
    if q:
        pattern = f"%{q}%"
        query = query.filter(
            or_(
                Transaction.note.ilike(pattern),
                Transaction.raw_description.ilike(pattern),
                Transaction.counterparty.ilike(pattern),
            )
        )
    if cursor is not None:
        cursor_date, cursor_id = _decode_cursor(cursor)
        query = query.filter(
            or_(
                Transaction.posted_at < cursor_date,
                (Transaction.posted_at == cursor_date) & (Transaction.id < cursor_id),
            )
        )

    rows = (
        query.order_by(Transaction.posted_at.desc(), Transaction.id.desc())
        .limit(limit + 1)
        .all()
    )
    next_cursor = None
    if len(rows) > limit:
        last = rows[limit - 1]
        next_cursor = _encode_cursor(last.posted_at, last.id)
        rows = rows[:limit]
    items = [TransactionRead.model_validate(row) for row in rows]
    return TransactionPage(items=items, next_cursor=next_cursor)


@router.post("/", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: TransactionCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Transaction:
    account = _get_owned_account(db, payload.account_id, current_user)
    _check_category(db, payload.category_id, current_user)

    category_id = payload.category_id
    if category_id is None:
        category_id = _autocategorize(db, current_user, payload.counterparty, payload.note)
    if category_id is None:
        category_id = uncategorized_category_id(db, payload.direction)

    currency = (payload.currency or account.currency).upper()
    fx_rate = None
    if currency == account.currency:
        amount_in_account_currency = payload.amount
    else:
        try:
            amount_in_account_currency, fx_rate = convert(
                db, payload.amount, currency, account.currency, payload.posted_at
            )
        except MissingFxRateError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    transaction = Transaction(
        account_id=payload.account_id,
        owner_id=current_user.id,
        amount=payload.amount,
        direction=payload.direction,
        posted_at=payload.posted_at,
        category_id=category_id,
        currency=currency,
        fx_rate_to_account_currency=fx_rate,
        amount_in_account_currency=amount_in_account_currency,
        counterparty=payload.counterparty,
        note=payload.note,
        source="manual",
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


@router.patch("/{transaction_id}", response_model=TransactionRead)
def update_transaction(
    transaction_id: int,
    payload: TransactionUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Transaction:
    transaction = _get_owned_transaction(db, transaction_id, current_user)
    if transaction.direction == "transfer":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede editar una transferencia; bórrala y créala de nuevo",
        )
    _check_category(db, payload.category_id, current_user)
    category_id = payload.category_id
    if category_id is None:
        category_id = uncategorized_category_id(db, payload.direction)

    transaction.amount = payload.amount
    transaction.direction = payload.direction
    transaction.posted_at = payload.posted_at
    transaction.category_id = category_id
    transaction.counterparty = payload.counterparty
    transaction.note = payload.note
    db.commit()
    db.refresh(transaction)
    return transaction


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    transaction = _get_owned_transaction(db, transaction_id, current_user)
    now = datetime.now(tz=transaction.created_at.tzinfo)
    if transaction.transfer_group_id is not None:
        siblings = (
            db.query(Transaction)
            .filter(
                Transaction.transfer_group_id == transaction.transfer_group_id,
                Transaction.owner_id == current_user.id,
                Transaction.deleted_at.is_(None),
            )
            .all()
        )
        for sibling in siblings:
            sibling.deleted_at = now
    else:
        transaction.deleted_at = now
    db.commit()


@router.post("/transfer", response_model=list[TransactionRead], status_code=status.HTTP_201_CREATED)
def create_transfer(
    payload: TransferCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[Transaction]:
    from_account = _get_owned_account(db, payload.from_account_id, current_user)
    to_account = _get_owned_account(db, payload.to_account_id, current_user)

    group_id = uuid.uuid4()
    outgoing = Transaction(
        account_id=from_account.id,
        owner_id=current_user.id,
        amount=-payload.amount,
        direction="transfer",
        posted_at=payload.posted_at,
        note=payload.note,
        source="manual",
        transfer_group_id=group_id,
    )
    incoming = Transaction(
        account_id=to_account.id,
        owner_id=current_user.id,
        amount=payload.amount,
        direction="transfer",
        posted_at=payload.posted_at,
        note=payload.note,
        source="manual",
        transfer_group_id=group_id,
    )
    db.add_all([outgoing, incoming])
    db.commit()
    db.refresh(outgoing)
    db.refresh(incoming)
    return [outgoing, incoming]


@router.post("/bulk-categorize", response_model=BulkCategorizeResult)
def bulk_categorize(
    payload: BulkCategorizeRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> BulkCategorizeResult:
    _check_category(db, payload.category_id, current_user)
    updated = (
        db.query(Transaction)
        .filter(
            Transaction.id.in_(payload.transaction_ids),
            Transaction.owner_id == current_user.id,
            Transaction.deleted_at.is_(None),
        )
        .update({"category_id": payload.category_id}, synchronize_session=False)
    )
    db.commit()
    return BulkCategorizeResult(updated_count=updated)
