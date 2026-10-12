import base64
import uuid
from datetime import date, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.core.openapi import AUTH_RESPONSES, Tag, error_responses
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
    TransactionTrashRead,
    TransactionUpdate,
    TransferCreate,
)
from app.services.categorizer import match_category, uncategorized_category_id
from app.services.fx import MissingFxRateError, convert
from app.services.notifications import check_budget_notifications
from app.services.transaction_retention import RETENTION_DAYS, purge_expired_transactions

router = APIRouter(prefix="/transactions", tags=[Tag.MOVIMIENTOS], responses=AUTH_RESPONSES)

TransactionId = Annotated[int, Path(description="Id del movimiento.", examples=[3233])]
_TRANSACTION_NOT_FOUND = "El movimiento no existe, está en la papelera o es de otro usuario."
_INVALID_TRANSACTION = (
    "Datos no válidos: signo del importe incoherente con `direction`, categoría raíz en lugar "
    "de subcategoría o falta el tipo de cambio para la moneda indicada.",
    "Una transacción debe asignarse a una subcategoría, no a la categoría principal",
)


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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
    if category.parent_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
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


@router.get(
    "/",
    response_model=TransactionPage,
    summary="Listar movimientos",
    responses=error_responses(400, e400=("El `cursor` no es válido.", "Cursor inválido")),
)
def list_transactions(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    account_id: Annotated[
        int | None, Query(description="Solo los de esta cuenta.", examples=[1110])
    ] = None,
    category_id: Annotated[
        int | None,
        Query(
            description="Solo los de esta categoría (no incluye sus subcategorías).",
            examples=[95],
        ),
    ] = None,
    direction: Annotated[
        str | None,
        Query(
            description="Solo los de este tipo: `income`, `expense` o `transfer`.",
            examples=["expense"],
        ),
    ] = None,
    date_from: Annotated[
        date | None, Query(description="Desde esta fecha (incluida).", examples=["2026-10-01"])
    ] = None,
    date_to: Annotated[
        date | None, Query(description="Hasta esta fecha (incluida).", examples=["2026-10-31"])
    ] = None,
    q: Annotated[
        str | None,
        Query(
            description="Texto a buscar (sin distinguir mayúsculas) en la nota, la descripción "
            "original y la contraparte.",
            examples=["mercadona"],
        ),
    ] = None,
    limit: Annotated[
        int, Query(ge=1, le=MAX_PAGE_SIZE, description="Tamaño de página (1–200).", examples=[50])
    ] = DEFAULT_PAGE_SIZE,
    cursor: Annotated[
        str | None,
        Query(description="`next_cursor` de la página anterior; omitir en la primera página."),
    ] = None,
) -> TransactionPage:
    """Movimientos no borrados del usuario, del más reciente al más antiguo,
    con filtros opcionales combinables. Paginación por cursor: si
    `next_cursor` no es `null`, hay más páginas."""
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
        query.order_by(Transaction.posted_at.desc(), Transaction.id.desc()).limit(limit + 1).all()
    )
    next_cursor = None
    if len(rows) > limit:
        last = rows[limit - 1]
        next_cursor = _encode_cursor(last.posted_at, last.id)
        rows = rows[:limit]
    items = [TransactionRead.model_validate(row) for row in rows]
    return TransactionPage(items=items, next_cursor=next_cursor)


@router.post(
    "/",
    response_model=TransactionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar movimiento",
    responses=error_responses(
        404,
        422,
        e404="La cuenta, o la categoría indicada, no existe o es de otro usuario.",
        e422=_INVALID_TRANSACTION,
    ),
)
def create_transaction(
    payload: TransactionCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Transaction:
    """Registra un ingreso o un gasto (las transferencias van por
    `POST /transactions/transfer`).

    - Sin `category_id`, se aplican las reglas de categorización sobre la
      contraparte (o la nota); si ninguna coincide, va a "Sin Clasificar".
    - Si `currency` difiere de la moneda de la cuenta, el importe se convierte
      con el tipo de cambio de esa fecha (`422` si no existe).
    - Después revisa los avisos de presupuesto del mes en curso."""
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
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
            ) from exc

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
    check_budget_notifications(db, current_user)
    return transaction


@router.patch(
    "/{transaction_id}",
    response_model=TransactionRead,
    summary="Editar movimiento",
    responses=error_responses(
        404,
        409,
        422,
        e404=_TRANSACTION_NOT_FOUND + " También si la categoría no es visible.",
        e409=(
            "Es una transferencia: no se puede editar.",
            "No se puede editar una transferencia; bórrala y créala de nuevo",
        ),
        e422=_INVALID_TRANSACTION,
    ),
)
def update_transaction(
    transaction_id: TransactionId,
    payload: TransactionUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Transaction:
    """Reemplaza importe, tipo, fecha, categoría, contraparte y nota (hay que
    enviarlos todos). Sin `category_id`, va a "Sin Clasificar". No cambia la
    cuenta ni la moneda. Después revisa los avisos de presupuesto."""
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
    check_budget_notifications(db, current_user)
    return transaction


@router.delete(
    "/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Mover movimiento a la papelera",
    responses=error_responses(404, e404=_TRANSACTION_NOT_FOUND),
)
def delete_transaction(
    transaction_id: TransactionId,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Borrado suave: el movimiento va a la papelera durante 30 días y
    después se elimina definitivamente. En una transferencia se borran los
    dos lados. Después revisa los avisos de presupuesto."""
    purge_expired_transactions(db)
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
    check_budget_notifications(db, current_user)


def _get_owned_trashed_transaction(
    db: Session, transaction_id: int, current_user: User
) -> Transaction:
    transaction = (
        db.query(Transaction)
        .filter(
            Transaction.id == transaction_id,
            Transaction.owner_id == current_user.id,
            Transaction.deleted_at.isnot(None),
        )
        .first()
    )
    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Movimiento no encontrado en la papelera"
        )
    return transaction


@router.get("/trash", response_model=list[TransactionTrashRead], summary="Listar la papelera")
def list_trash(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[TransactionTrashRead]:
    """Movimientos borrados en los últimos 30 días, del borrado más reciente
    al más antiguo, con la fecha en que se eliminarán definitivamente. Antes
    de responder purga los que ya caducaron."""
    purge_expired_transactions(db)
    rows = (
        db.query(Transaction)
        .filter(Transaction.owner_id == current_user.id, Transaction.deleted_at.isnot(None))
        .order_by(Transaction.deleted_at.desc())
        .all()
    )
    items = []
    for row in rows:
        base = TransactionRead.model_validate(row).model_dump()
        deleted_at = row.deleted_at
        assert deleted_at is not None  # la consulta solo trae movimientos borrados
        items.append(
            TransactionTrashRead(
                **base,
                deleted_at=deleted_at,
                purge_at=deleted_at + timedelta(days=RETENTION_DAYS),
            )
        )
    return items


@router.post(
    "/{transaction_id}/restore",
    response_model=TransactionRead,
    summary="Restaurar desde la papelera",
    responses=error_responses(
        404,
        e404=(
            "El movimiento no está en la papelera (ya caducó o no existe).",
            "Movimiento no encontrado en la papelera",
        ),
    ),
)
def restore_transaction(
    transaction_id: TransactionId,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Transaction:
    """Saca el movimiento de la papelera (en una transferencia, los dos
    lados). Después revisa los avisos de presupuesto."""
    purge_expired_transactions(db)
    transaction = _get_owned_trashed_transaction(db, transaction_id, current_user)
    if transaction.transfer_group_id is not None:
        siblings = (
            db.query(Transaction)
            .filter(
                Transaction.transfer_group_id == transaction.transfer_group_id,
                Transaction.owner_id == current_user.id,
                Transaction.deleted_at.isnot(None),
            )
            .all()
        )
        for sibling in siblings:
            sibling.deleted_at = None
    else:
        transaction.deleted_at = None
    db.commit()
    db.refresh(transaction)
    check_budget_notifications(db, current_user)
    return transaction


@router.post(
    "/transfer",
    response_model=list[TransactionRead],
    status_code=status.HTTP_201_CREATED,
    summary="Registrar transferencia entre cuentas",
    responses=error_responses(
        404, e404="Alguna de las dos cuentas no existe o es de otro usuario."
    ),
)
def create_transfer(
    payload: TransferCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[Transaction]:
    """Crea dos movimientos de tipo `transfer` enlazados por
    `transfer_group_id`: la salida (negativa) en la cuenta de origen y la
    entrada (positiva) en la de destino. No cuentan como ingreso ni gasto."""
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


@router.post(
    "/bulk-categorize",
    response_model=BulkCategorizeResult,
    summary="Recategorizar movimientos en bloque",
    responses=error_responses(
        404,
        422,
        e404="La categoría no existe o es de otro usuario.",
        e422=_INVALID_TRANSACTION,
    ),
)
def bulk_categorize(
    payload: BulkCategorizeRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> BulkCategorizeResult:
    """Asigna una subcategoría a varios movimientos. Los ids que no existen,
    están en la papelera o son de otro usuario se ignoran (`updated_count`
    dice cuántos cambiaron). Después revisa los avisos de presupuesto."""
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
    check_budget_notifications(db, current_user)
    return BulkCategorizeResult(updated_count=updated)
