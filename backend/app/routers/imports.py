from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.account import Account
from app.models.categorization_rule import CategorizationRule
from app.models.import_batch import ImportBatch
from app.models.import_row import ImportRow
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.imports import (
    ImportCommitRequest,
    ImportCommitResult,
    ImportPreview,
    ImportRowRead,
)
from app.services.categorizer import match_category, uncategorized_category_id
from app.services.notifications import check_budget_notifications
from app.services.reconciler import external_hash, find_probable_duplicate
from app.services.statement_parser import StatementParseError, parse_csv

router = APIRouter(prefix="/imports", tags=["imports"])

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
MAX_ROWS = 10_000


def _get_owned_account(db: Session, account_id: int, current_user: User) -> Account:
    account = (
        db.query(Account)
        .filter(Account.id == account_id, Account.owner_id == current_user.id)
        .first()
    )
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada")
    return account


def _get_owned_batch(db: Session, batch_id: int, current_user: User) -> ImportBatch:
    batch = (
        db.query(ImportBatch)
        .filter(ImportBatch.id == batch_id, ImportBatch.owner_id == current_user.id)
        .first()
    )
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Importación no encontrada")
    return batch


def _to_preview(batch: ImportBatch, rows: list[ImportRow]) -> ImportPreview:
    new_count = sum(1 for r in rows if r.classification == "NEW")
    exact_count = sum(1 for r in rows if r.classification == "EXACT_DUPLICATE")
    probable_count = sum(1 for r in rows if r.classification == "PROBABLE_DUPLICATE")
    return ImportPreview(
        id=batch.id,
        account_id=batch.account_id,
        filename=batch.filename,
        status=batch.status,
        range_start=batch.range_start,
        range_end=batch.range_end,
        created_at=batch.created_at,
        new_count=new_count,
        exact_duplicate_count=exact_count,
        probable_duplicate_count=probable_count,
        rows=[ImportRowRead.model_validate(r) for r in rows],
    )


@router.post("/", response_model=ImportPreview, status_code=status.HTTP_201_CREATED)
async def upload_statement(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    account_id: Annotated[int, Form()],
    file: Annotated[UploadFile, File()],
) -> ImportPreview:
    account = _get_owned_account(db, account_id, current_user)

    filename = file.filename or "extracto.csv"
    if not filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Por ahora solo se admite CSV; XLSX y PDF llegarán en un cambio posterior",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="El archivo supera el límite de 5 MB",
        )

    try:
        parsed_rows = parse_csv(content)
    except StatementParseError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    if len(parsed_rows) > MAX_ROWS:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"El archivo supera el límite de {MAX_ROWS} filas",
        )

    range_start = min(r.posted_at for r in parsed_rows)
    range_end = max(r.posted_at for r in parsed_rows)

    existing = (
        db.query(Transaction)
        .filter(
            Transaction.account_id == account.id,
            Transaction.owner_id == current_user.id,
            Transaction.deleted_at.is_(None),
            # ±1 día de margen sobre el rango del archivo: el match difuso
            # tolera esa diferencia de fecha (ver reconciler.py).
            Transaction.posted_at >= range_start - timedelta(days=1),
            Transaction.posted_at <= range_end + timedelta(days=1),
        )
        .all()
    )
    existing_by_hash = {
        external_hash(account.id, tx.posted_at, tx.amount, tx.raw_description or tx.note or ""): tx
        for tx in existing
    }

    batch = ImportBatch(
        owner_id=current_user.id,
        account_id=account.id,
        filename=filename,
        status="previewed",
        range_start=range_start,
        range_end=range_end,
    )
    db.add(batch)
    db.flush()

    for parsed in parsed_rows:
        row_hash = external_hash(account.id, parsed.posted_at, parsed.amount, parsed.raw_description)
        matched = existing_by_hash.get(row_hash)
        if matched is not None:
            classification, matched_id = "EXACT_DUPLICATE", matched.id
        else:
            probable = find_probable_duplicate(
                parsed.posted_at, parsed.amount, parsed.raw_description, existing
            )
            if probable is not None:
                classification, matched_id = "PROBABLE_DUPLICATE", probable.id
            else:
                classification, matched_id = "NEW", None

        db.add(
            ImportRow(
                batch_id=batch.id,
                posted_at=parsed.posted_at,
                amount=parsed.amount,
                raw_description=parsed.raw_description,
                external_hash=row_hash,
                classification=classification,
                matched_transaction_id=matched_id,
            )
        )

    db.commit()
    db.refresh(batch)
    rows = (
        db.query(ImportRow)
        .filter(ImportRow.batch_id == batch.id)
        .order_by(ImportRow.posted_at, ImportRow.id)
        .all()
    )
    return _to_preview(batch, rows)


@router.get("/{batch_id}", response_model=ImportPreview)
def get_import(
    batch_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ImportPreview:
    batch = _get_owned_batch(db, batch_id, current_user)
    rows = (
        db.query(ImportRow)
        .filter(ImportRow.batch_id == batch.id)
        .order_by(ImportRow.posted_at, ImportRow.id)
        .all()
    )
    return _to_preview(batch, rows)


@router.post("/{batch_id}/commit", response_model=ImportCommitResult)
def commit_import(
    batch_id: int,
    payload: ImportCommitRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ImportCommitResult:
    batch = _get_owned_batch(db, batch_id, current_user)
    if batch.status == "committed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Esta importación ya fue confirmada"
        )

    rows = db.query(ImportRow).filter(ImportRow.batch_id == batch.id).all()
    row_ids = set(payload.row_ids)
    now = datetime.now(timezone.utc)
    replaced_count = 0

    if payload.strategy == "replace_range":
        replaced_count = (
            db.query(Transaction)
            .filter(
                Transaction.account_id == batch.account_id,
                Transaction.owner_id == current_user.id,
                Transaction.deleted_at.is_(None),
                Transaction.posted_at >= batch.range_start,
                Transaction.posted_at <= batch.range_end,
                Transaction.source.in_(("import", "rule")),
            )
            .update({"deleted_at": now}, synchronize_session=False)
        )
        rows_to_insert = rows
    elif payload.strategy == "replace_selected":
        matched_ids = [
            r.matched_transaction_id
            for r in rows
            if r.id in row_ids and r.matched_transaction_id is not None
        ]
        if matched_ids:
            replaced_count = (
                db.query(Transaction)
                .filter(
                    Transaction.id.in_(matched_ids),
                    Transaction.source.in_(("import", "rule")),
                )
                .update({"deleted_at": now}, synchronize_session=False)
            )
        rows_to_insert = [r for r in rows if r.classification == "NEW" or r.id in row_ids]
    else:  # append_new
        rows_to_insert = [r for r in rows if r.classification == "NEW" or r.id in row_ids]

    skipped_count = len(rows) - len(rows_to_insert)

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

    inserted_count = 0
    for row in rows_to_insert:
        direction = "expense" if row.amount < 0 else "income"
        category_id = match_category(row.raw_description, rules)
        if category_id is None:
            category_id = uncategorized_category_id(db, direction)
        transaction = Transaction(
            account_id=batch.account_id,
            owner_id=current_user.id,
            amount=row.amount,
            direction=direction,
            posted_at=row.posted_at,
            category_id=category_id,
            raw_description=row.raw_description,
            source="import",
        )
        db.add(transaction)
        db.flush()
        row.created_transaction_id = transaction.id
        inserted_count += 1

    batch.status = "committed"
    batch.strategy = payload.strategy
    batch.inserted_count = inserted_count
    batch.replaced_count = replaced_count
    batch.skipped_count = skipped_count
    batch.committed_at = now
    db.commit()
    check_budget_notifications(db, current_user)

    return ImportCommitResult(
        id=batch.id,
        status=batch.status,
        strategy=payload.strategy,
        inserted_count=inserted_count,
        replaced_count=replaced_count,
        skipped_count=skipped_count,
    )
