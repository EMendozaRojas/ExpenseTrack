import io
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Path, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.core.openapi import AUTH_RESPONSES, Tag, error_responses
from app.models.attachment import Attachment
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.attachment import AttachmentRead
from app.services.file_signature import content_disposition, detect_mime, safe_filename
from app.services.storage import get_storage_backend

router = APIRouter(tags=[Tag.ADJUNTOS], responses=AUTH_RESPONSES)

TransactionId = Annotated[int, Path(description="Id del movimiento.", examples=[3233])]
AttachmentId = Annotated[int, Path(description="Id del adjunto.", examples=[15])]
_TRANSACTION_NOT_FOUND = (
    "El movimiento no existe o es de otro usuario.",
    "Movimiento no encontrado",
)
_ATTACHMENT_NOT_FOUND = ("El adjunto no existe o es de otro usuario.", "Adjunto no encontrado")

MAX_ATTACHMENT_SIZE_BYTES = 10 * 1024 * 1024
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}


def _get_owned_transaction(db: Session, transaction_id: int, current_user: User) -> Transaction:
    transaction = (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id, Transaction.owner_id == current_user.id)
        .first()
    )
    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Movimiento no encontrado"
        )
    return transaction


def _get_owned_attachment(db: Session, attachment_id: int, current_user: User) -> Attachment:
    attachment = (
        db.query(Attachment)
        .filter(Attachment.id == attachment_id, Attachment.owner_id == current_user.id)
        .first()
    )
    if attachment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Adjunto no encontrado")
    return attachment


@router.post(
    "/transactions/{transaction_id}/attachments",
    response_model=AttachmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Adjuntar un archivo a un movimiento",
    responses=error_responses(
        404,
        413,
        415,
        422,
        e404=_TRANSACTION_NOT_FOUND,
        e413=("El archivo supera los 10 MB.", "El archivo supera el límite de 10 MB"),
        e415=(
            "El archivo no es JPEG, PNG, WebP ni PDF, o su contenido no coincide con el "
            "tipo declarado.",
            "Solo se admiten imágenes (JPEG/PNG/WebP) o PDF",
        ),
        e422=("El archivo está vacío.", "Archivo vacío"),
    ),
)
async def upload_attachment(
    transaction_id: TransactionId,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    file: Annotated[
        UploadFile, File(description="Recibo o documento: JPEG, PNG, WebP o PDF de hasta 10 MB.")
    ],
) -> AttachmentRead:
    """Sube un recibo o documento (`multipart/form-data`) y lo asocia al
    movimiento. Un movimiento puede tener varios adjuntos."""
    transaction = _get_owned_transaction(db, transaction_id, current_user)

    mime_type = file.content_type or "application/octet-stream"
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Solo se admiten imágenes (JPEG/PNG/WebP) o PDF",
        )

    content = await file.read()
    if len(content) > MAX_ATTACHMENT_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="El archivo supera el límite de 10 MB",
        )
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Archivo vacío"
        )
    if detect_mime(content) != mime_type:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="El contenido del archivo no coincide con su tipo",
        )

    storage_key = uuid.uuid4().hex
    get_storage_backend().save(storage_key, io.BytesIO(content))

    attachment = Attachment(
        transaction_id=transaction.id,
        owner_id=current_user.id,
        storage_key=storage_key,
        filename=safe_filename(file.filename),
        mime_type=mime_type,
        size_bytes=len(content),
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return AttachmentRead.model_validate(attachment)


@router.get(
    "/transactions/{transaction_id}/attachments",
    response_model=list[AttachmentRead],
    summary="Listar los adjuntos de un movimiento",
    responses=error_responses(404, e404=_TRANSACTION_NOT_FOUND),
)
def list_attachments(
    transaction_id: TransactionId,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[AttachmentRead]:
    """Adjuntos del movimiento, del más antiguo al más reciente (solo los
    datos; el archivo se descarga con `GET /attachments/{attachment_id}`)."""
    transaction = _get_owned_transaction(db, transaction_id, current_user)
    attachments = (
        db.query(Attachment)
        .filter(Attachment.transaction_id == transaction.id)
        .order_by(Attachment.created_at)
        .all()
    )
    return [AttachmentRead.model_validate(a) for a in attachments]


@router.get(
    "/attachments/{attachment_id}",
    response_class=StreamingResponse,
    summary="Descargar un adjunto",
    responses={
        200: {
            "description": "El archivo, con su tipo de contenido original y "
            "`Content-Disposition: inline`.",
            "content": {
                "image/jpeg": {},
                "image/png": {},
                "image/webp": {},
                "application/pdf": {},
            },
        },
        **error_responses(404, e404=_ATTACHMENT_NOT_FOUND),
    },
)
def download_attachment(
    attachment_id: AttachmentId,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> StreamingResponse:
    """Devuelve el archivo del adjunto (no JSON)."""
    attachment = _get_owned_attachment(db, attachment_id, current_user)
    file_handle = get_storage_backend().open(attachment.storage_key)
    return StreamingResponse(
        file_handle,
        media_type=attachment.mime_type,
        headers={
            "Content-Disposition": content_disposition(attachment.filename),
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.delete(
    "/attachments/{attachment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Borrar un adjunto",
    responses=error_responses(404, e404=_ATTACHMENT_NOT_FOUND),
)
def delete_attachment(
    attachment_id: AttachmentId,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Borra el adjunto y su archivo de forma definitiva."""
    attachment = _get_owned_attachment(db, attachment_id, current_user)
    get_storage_backend().delete(attachment.storage_key)
    db.delete(attachment)
    db.commit()
