import io
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.core.openapi import AUTH_RESPONSES, Tag, error_responses
from app.models.user import User
from app.schemas.user import UserProfileUpdate, UserRead
from app.services.storage import get_storage_backend

router = APIRouter(prefix="/users/me", tags=[Tag.USUARIO], responses=AUTH_RESPONSES)

MAX_AVATAR_SIZE_BYTES = 5 * 1024 * 1024
ALLOWED_AVATAR_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.patch("/", response_model=UserRead, summary="Actualizar el perfil")
def update_profile(
    payload: UserProfileUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Cambia el nombre del usuario. Los campos que no se envían no cambian."""
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post(
    "/avatar",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Subir la foto de perfil",
    responses=error_responses(
        413,
        415,
        422,
        e413=("La imagen supera los 5 MB.", "La foto de perfil supera el límite de 5 MB"),
        e415=("La imagen no es JPEG, PNG ni WebP.", "Solo se admiten imágenes JPEG, PNG o WebP"),
        e422=("El archivo está vacío.", "Archivo vacío"),
    ),
)
async def upload_avatar(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    file: Annotated[UploadFile, File(description="Imagen JPEG, PNG o WebP de hasta 5 MB.")],
) -> User:
    """Sube o reemplaza la foto de perfil (`multipart/form-data`). La foto
    anterior se borra."""
    mime_type = file.content_type or "application/octet-stream"
    if mime_type not in ALLOWED_AVATAR_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Solo se admiten imágenes JPEG, PNG o WebP",
        )

    content = await file.read()
    if len(content) > MAX_AVATAR_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="La foto de perfil supera el límite de 5 MB",
        )
    if len(content) == 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Archivo vacío")

    storage = get_storage_backend()
    old_key = current_user.avatar_storage_key

    new_key = uuid.uuid4().hex
    storage.save(new_key, io.BytesIO(content))

    current_user.avatar_storage_key = new_key
    current_user.avatar_mime_type = mime_type
    db.commit()
    db.refresh(current_user)

    if old_key:
        storage.delete(old_key)

    return current_user


@router.get(
    "/avatar",
    response_class=StreamingResponse,
    summary="Descargar la foto de perfil",
    responses={
        200: {
            "description": "La imagen, con su tipo de contenido original.",
            "content": {"image/jpeg": {}, "image/png": {}, "image/webp": {}},
        },
        **error_responses(404, e404=("El usuario no tiene foto de perfil.", "Sin foto de perfil")),
    },
)
def get_avatar(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> StreamingResponse:
    """Devuelve el archivo de la foto de perfil (no JSON)."""
    if current_user.avatar_storage_key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sin foto de perfil")
    file_handle = get_storage_backend().open(current_user.avatar_storage_key)
    return StreamingResponse(
        file_handle,
        media_type=current_user.avatar_mime_type or "application/octet-stream",
    )


@router.delete(
    "/avatar", status_code=status.HTTP_204_NO_CONTENT, summary="Borrar la foto de perfil"
)
def delete_avatar(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Borra la foto de perfil. Responde `204` aunque no hubiera ninguna."""
    if current_user.avatar_storage_key is not None:
        get_storage_backend().delete(current_user.avatar_storage_key)
        current_user.avatar_storage_key = None
        current_user.avatar_mime_type = None
        db.commit()
