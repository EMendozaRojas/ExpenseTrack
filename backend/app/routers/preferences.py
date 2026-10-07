from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.core.openapi import AUTH_RESPONSES, Tag, error_responses
from app.models.transaction import Transaction
from app.models.user import User
from app.models.user_preference import UserPreferences
from app.schemas.preferences import UserPreferencesRead, UserPreferencesUpdate

router = APIRouter(
    prefix="/users/me/preferences", tags=[Tag.PREFERENCIAS], responses=AUTH_RESPONSES
)


def _get_or_create(db: Session, current_user: User) -> UserPreferences:
    preferences = (
        db.query(UserPreferences).filter(UserPreferences.owner_id == current_user.id).first()
    )
    if preferences is None:
        preferences = UserPreferences(owner_id=current_user.id)
        db.add(preferences)
        db.commit()
        db.refresh(preferences)
    return preferences


def _has_transactions(db: Session, current_user: User) -> bool:
    return (
        db.query(Transaction.id)
        .filter(Transaction.owner_id == current_user.id, Transaction.deleted_at.is_(None))
        .first()
        is not None
    )


def _to_read(db: Session, current_user: User, preferences: UserPreferences) -> UserPreferencesRead:
    return UserPreferencesRead(
        base_currency=preferences.base_currency,
        locale=preferences.locale,
        has_transactions=_has_transactions(db, current_user),
    )


@router.get("/", response_model=UserPreferencesRead, summary="Ver las preferencias")
def get_preferences(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserPreferencesRead:
    """Devuelve las preferencias del usuario. Si aún no tiene, se crean con
    los valores por defecto."""
    return _to_read(db, current_user, _get_or_create(db, current_user))


@router.patch(
    "/",
    response_model=UserPreferencesRead,
    summary="Actualizar las preferencias",
    responses=error_responses(
        409,
        e409=(
            "Se intentó cambiar la moneda base y el usuario ya tiene movimientos.",
            "No puedes cambiar la moneda principal porque ya tienes movimientos registrados.",
        ),
    ),
)
def update_preferences(
    payload: UserPreferencesUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserPreferencesRead:
    """Cambia la moneda base o el idioma. Los campos que no se envían no
    cambian. La moneda base solo se puede cambiar mientras el usuario no
    tenga movimientos."""
    preferences = _get_or_create(db, current_user)
    if payload.base_currency is not None:
        if _has_transactions(db, current_user):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No puedes cambiar la moneda principal porque ya tienes movimientos registrados.",
            )
        preferences.base_currency = payload.base_currency
    if payload.locale is not None:
        preferences.locale = payload.locale
    db.commit()
    db.refresh(preferences)
    return _to_read(db, current_user, preferences)
