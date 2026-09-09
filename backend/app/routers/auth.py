from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.security import create_access_token, hash_password, verify_password
from app.core.config import get_settings
from app.core.database import get_db
from app.models.auth_identity import AuthIdentity
from app.models.user import User
from app.schemas.token import LogoutRequest, RefreshRequest, Token
from app.schemas.user import UserCreate, UserRead
from app.services import google_oauth
from app.services.refresh_tokens import (
    get_valid_refresh_token,
    issue_refresh_token,
    revoke_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Annotated[Session, Depends(get_db)]) -> User:
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="El email ya está registrado"
        )
    user = User(email=payload.email, hashed_password=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
) -> Token:
    user = db.query(User).filter(User.email == form_data.username).first()
    if (
        user is None
        or user.hashed_password is None
        or not verify_password(form_data.password, user.hashed_password)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    refresh_token = issue_refresh_token(db, user.id)
    return Token(access_token=create_access_token(subject=str(user.id)), refresh_token=refresh_token)


@router.post("/refresh", response_model=Token)
def refresh(payload: RefreshRequest, db: Annotated[Session, Depends(get_db)]) -> Token:
    record = get_valid_refresh_token(db, payload.refresh_token)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido o expirado"
        )
    revoke_refresh_token(db, record)
    new_refresh_token = issue_refresh_token(db, record.user_id)
    return Token(
        access_token=create_access_token(subject=str(record.user_id)),
        refresh_token=new_refresh_token,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: LogoutRequest, db: Annotated[Session, Depends(get_db)]) -> None:
    record = get_valid_refresh_token(db, payload.refresh_token)
    if record is not None:
        revoke_refresh_token(db, record)


@router.get("/me", response_model=UserRead)
def me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user


@router.get("/oauth/google/start")
def google_oauth_start() -> RedirectResponse:
    settings = get_settings()
    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Login con Google no está configurado en este entorno",
        )
    return RedirectResponse(google_oauth.build_authorize_url())


@router.get("/oauth/google/callback")
async def google_oauth_callback(
    code: str,
    state: str,
    db: Annotated[Session, Depends(get_db)],
) -> RedirectResponse:
    settings = get_settings()
    if not google_oauth.verify_state(state):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="state inválido o expirado")

    try:
        userinfo = await google_oauth.exchange_code_for_userinfo(code)
    except google_oauth.OAuthError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    provider_uid = userinfo.get("sub")
    email = userinfo.get("email")
    if not provider_uid or not email:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="Google no devolvió sub/email"
        )

    identity = (
        db.query(AuthIdentity)
        .filter(AuthIdentity.provider == "google", AuthIdentity.provider_uid == provider_uid)
        .first()
    )
    if identity is not None:
        user = db.query(User).filter(User.id == identity.user_id).first()
    else:
        # Google verifica la propiedad del email: si ya existe una cuenta
        # con ese email, se liga la identidad automáticamente en vez de
        # pedir un paso extra de confirmación (recorte de alcance del MVP).
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            user = User(email=email, hashed_password=None)
            db.add(user)
            db.flush()
        db.add(AuthIdentity(user_id=user.id, provider="google", provider_uid=provider_uid, email=email))
        db.commit()

    if user is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No se pudo resolver el usuario")

    access_token = create_access_token(subject=str(user.id))
    refresh_token = issue_refresh_token(db, user.id)
    redirect_url = (
        f"{settings.frontend_base_url}/auth/social-callback"
        f"?access_token={access_token}&refresh_token={refresh_token}"
    )
    return RedirectResponse(redirect_url)
