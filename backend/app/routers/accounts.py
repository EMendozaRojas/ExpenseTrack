from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.account import AccountCreate, AccountRead, AccountUpdate

router = APIRouter(prefix="/accounts", tags=["accounts"])


def _balance(db: Session, account: Account) -> Decimal:
    spent: Decimal = (
        db.query(func.coalesce(func.sum(Transaction.amount), Decimal("0")))
        .filter(Transaction.account_id == account.id, Transaction.deleted_at.is_(None))
        .scalar()
    )
    return account.initial_balance + spent


def _to_read(db: Session, account: Account) -> AccountRead:
    return AccountRead.model_validate(
        {**account.__dict__, "balance": _balance(db, account)}, from_attributes=True
    )


def _get_owned_account(db: Session, account_id: int, current_user: User) -> Account:
    account = (
        db.query(Account)
        .filter(Account.id == account_id, Account.owner_id == current_user.id)
        .first()
    )
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada")
    return account


@router.get("/", response_model=list[AccountRead])
def list_accounts(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[AccountRead]:
    accounts = (
        db.query(Account)
        .filter(Account.owner_id == current_user.id, Account.is_archived.is_(False))
        .order_by(Account.name)
        .all()
    )
    return [_to_read(db, account) for account in accounts]


@router.post("/", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(
    payload: AccountCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AccountRead:
    account = Account(
        owner_id=current_user.id,
        name=payload.name,
        type=payload.type,
        currency=payload.currency.upper(),
        initial_balance=payload.initial_balance,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return _to_read(db, account)


@router.patch("/{account_id}", response_model=AccountRead)
def update_account(
    account_id: int,
    payload: AccountUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AccountRead:
    account = _get_owned_account(db, account_id, current_user)
    if payload.name is not None:
        account.name = payload.name
    if payload.type is not None:
        account.type = payload.type
    if payload.currency is not None:
        account.currency = payload.currency.upper()
    db.commit()
    db.refresh(account)
    return _to_read(db, account)


@router.post("/{account_id}/archive", response_model=AccountRead)
def archive_account(
    account_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AccountRead:
    account = _get_owned_account(db, account_id, current_user)
    account.is_archived = True
    db.commit()
    db.refresh(account)
    return _to_read(db, account)


@router.get("/{account_id}/balance")
def get_account_balance(
    account_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Decimal]:
    account = _get_owned_account(db, account_id, current_user)
    return {"balance": _balance(db, account)}
