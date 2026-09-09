from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.user_preference import UserPreferences
from app.schemas.preferences import UserPreferencesRead, UserPreferencesUpdate

router = APIRouter(prefix="/users/me/preferences", tags=["preferences"])


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


@router.get("/", response_model=UserPreferencesRead)
def get_preferences(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserPreferencesRead:
    return UserPreferencesRead.model_validate(_get_or_create(db, current_user))


@router.patch("/", response_model=UserPreferencesRead)
def update_preferences(
    payload: UserPreferencesUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserPreferencesRead:
    preferences = _get_or_create(db, current_user)
    if payload.base_currency is not None:
        preferences.base_currency = payload.base_currency
    if payload.locale is not None:
        preferences.locale = payload.locale
    db.commit()
    db.refresh(preferences)
    return UserPreferencesRead.model_validate(preferences)
