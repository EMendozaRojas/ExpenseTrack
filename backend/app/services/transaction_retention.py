"""Papelera de movimientos: borrado lógico con caducidad.

Al borrar un movimiento solo se marca `deleted_at` (ver `routers/transactions.py`).
Se conserva 30 días por si el usuario quiere recuperarlo; pasado ese plazo se
borra en firme (y con él, sus adjuntos) mediante `purge_expired_transactions`.

No hay infraestructura de jobs periódicos en este proyecto (sin scheduler),
así que el purgado se dispara de forma perezosa al entrar a los endpoints de
papelera/restaurar/borrar, igual que otros "creados perezosamente" del
proyecto (p. ej. `user_preferences`).
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.attachment import Attachment
from app.models.transaction import Transaction
from app.services.storage import get_storage_backend

RETENTION_DAYS = 30


def purge_expired_transactions(db: Session) -> int:
    cutoff = datetime.now(UTC) - timedelta(days=RETENTION_DAYS)
    expired = (
        db.query(Transaction)
        .filter(Transaction.deleted_at.isnot(None), Transaction.deleted_at < cutoff)
        .all()
    )
    if not expired:
        return 0

    storage = get_storage_backend()
    for transaction in expired:
        attachments = db.query(Attachment).filter(Attachment.transaction_id == transaction.id).all()
        for attachment in attachments:
            storage.delete(attachment.storage_key)
            db.delete(attachment)
        db.delete(transaction)

    db.commit()
    return len(expired)
