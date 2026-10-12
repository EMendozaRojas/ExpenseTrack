from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.core.openapi import AUTH_RESPONSES, Tag, error_responses
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.account import AccountBalance, AccountCreate, AccountRead, AccountUpdate

router = APIRouter(prefix="/accounts", tags=[Tag.CUENTAS], responses=AUTH_RESPONSES)

AccountId = Annotated[int, Path(description="Id de la cuenta.", examples=[1110])]
NOT_FOUND = error_responses(
    404, e404=("La cuenta no existe o es de otro usuario.", "Cuenta no encontrada")
)


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


def _clear_other_primary_accounts(
    db: Session, current_user: User, except_account_id: int | None
) -> None:
    query = db.query(Account).filter(
        Account.owner_id == current_user.id, Account.is_primary.is_(True)
    )
    if except_account_id is not None:
        query = query.filter(Account.id != except_account_id)
    query.update({"is_primary": False})


def _get_owned_account(db: Session, account_id: int, current_user: User) -> Account:
    account = (
        db.query(Account)
        .filter(Account.id == account_id, Account.owner_id == current_user.id)
        .first()
    )
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada")
    return account


@router.get("/", response_model=list[AccountRead], summary="Listar cuentas")
def list_accounts(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[AccountRead]:
    """Cuentas del usuario que no están archivadas, por nombre, con su saldo
    actual."""
    accounts = (
        db.query(Account)
        .filter(Account.owner_id == current_user.id, Account.is_archived.is_(False))
        .order_by(Account.name)
        .all()
    )
    return [_to_read(db, account) for account in accounts]


@router.post(
    "/", response_model=AccountRead, status_code=status.HTTP_201_CREATED, summary="Crear cuenta"
)
def create_account(
    payload: AccountCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AccountRead:
    """Crea una cuenta. Si se marca como principal, las demás dejan de serlo
    (solo hay una cuenta principal por usuario)."""
    account = Account(
        owner_id=current_user.id,
        name=payload.name,
        type=payload.type,
        currency=payload.currency.upper(),
        initial_balance=payload.initial_balance,
        is_primary=payload.is_primary,
    )
    db.add(account)
    db.flush()
    if payload.is_primary:
        _clear_other_primary_accounts(db, current_user, account.id)
    db.commit()
    db.refresh(account)
    return _to_read(db, account)


@router.patch(
    "/{account_id}", response_model=AccountRead, summary="Editar cuenta", responses=NOT_FOUND
)
def update_account(
    account_id: AccountId,
    payload: AccountUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AccountRead:
    """Cambia nombre, tipo, moneda o si es la principal. Los campos que no se
    envían no cambian. El saldo inicial no se puede editar."""
    account = _get_owned_account(db, account_id, current_user)
    if payload.name is not None:
        account.name = payload.name
    if payload.type is not None:
        account.type = payload.type
    if payload.currency is not None:
        account.currency = payload.currency.upper()
    if payload.is_primary is not None:
        account.is_primary = payload.is_primary
        if payload.is_primary:
            _clear_other_primary_accounts(db, current_user, account.id)
    db.commit()
    db.refresh(account)
    return _to_read(db, account)


@router.post(
    "/{account_id}/archive",
    response_model=AccountRead,
    summary="Archivar cuenta",
    responses=NOT_FOUND,
)
def archive_account(
    account_id: AccountId,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AccountRead:
    """Oculta la cuenta del listado. Sus movimientos se conservan. No hay
    endpoint para desarchivar."""
    account = _get_owned_account(db, account_id, current_user)
    account.is_archived = True
    db.commit()
    db.refresh(account)
    return _to_read(db, account)


@router.get(
    "/{account_id}/balance",
    response_model=AccountBalance,
    summary="Ver el saldo de una cuenta",
    responses=NOT_FOUND,
)
def get_account_balance(
    account_id: AccountId,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AccountBalance:
    """Saldo actual: saldo inicial más la suma de los movimientos no
    borrados de la cuenta, en la moneda de la cuenta."""
    account = _get_owned_account(db, account_id, current_user)
    return AccountBalance(balance=_balance(db, account))
