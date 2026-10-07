from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.security import create_access_token, hash_password, verify_password
from app.core.config import get_settings
from app.core.database import get_db
from app.core.openapi import AUTH_RESPONSES, Tag, error_responses
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

router = APIRouter(prefix="/auth", tags=[Tag.AUTENTICACION])

_UNUSED_OAUTH2_FIELD = "No se usa; se acepta por compatibilidad con OAuth2."


class LoginForm(OAuth2PasswordRequestForm):
    """El formulario OAuth2 estándar (mismos campos y validación), con los
    campos documentados en español."""

    def __init__(
        self,
        *,
        grant_type: Annotated[
            str | None,
            Form(
                pattern="password",
                description="Tipo de concesión OAuth2. Si se envía, debe ser `password`.",
                examples=["password"],
            ),
        ] = None,
        username: Annotated[
            str,
            Form(description="Email del usuario.", examples=["demo.datos@example.com"]),
        ],
        password: Annotated[
            str, Form(description="Contraseña del usuario.", examples=["demodatos1234"])
        ],
        scope: Annotated[
            str, Form(description=_UNUSED_OAUTH2_FIELD, examples=[""])
        ] = "",
        client_id: Annotated[
            str | None,
            Form(description=_UNUSED_OAUTH2_FIELD, examples=[None]),
        ] = None,
        client_secret: Annotated[
            str | None,
            Form(description=_UNUSED_OAUTH2_FIELD, examples=[None]),
        ] = None,
    ):
        super().__init__(
            grant_type=grant_type,
            username=username,
            password=password,
            scope=scope,
            client_id=client_id,
            client_secret=client_secret,
        )


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar usuario",
    responses=error_responses(
        409, e409=("El email ya está registrado.", "El email ya está registrado")
    ),
)
def register(payload: UserCreate, db: Annotated[Session, Depends(get_db)]) -> User:
    """Crea una cuenta con email y contraseña. No inicia sesión: después hay
    que llamar a `POST /auth/login`. El nombre se completa luego en el
    onboarding (`PATCH /users/me/`)."""
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


@router.post(
    "/login",
    response_model=Token,
    summary="Iniciar sesión",
    responses=error_responses(
        401, e401=("Email o contraseña incorrectos.", "Email o contraseña incorrectos")
    ),
)
def login(
    form_data: Annotated[LoginForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
) -> Token:
    """Login con email y contraseña (formulario
    `application/x-www-form-urlencoded`, flujo OAuth2 *password*). Devuelve un
    token de acceso de corta duración y un refresh token para renovarlo.

    Es el endpoint que usa el botón **Authorize** de esta documentación.
    Las cuentas creadas solo con Google no tienen contraseña y no pueden
    entrar por aquí."""
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


@router.post(
    "/refresh",
    response_model=Token,
    summary="Renovar el token de acceso",
    responses=error_responses(
        401,
        e401=("El refresh token no existe, está revocado o ha caducado.",
              "Refresh token inválido o expirado"),
    ),
)
def refresh(payload: RefreshRequest, db: Annotated[Session, Depends(get_db)]) -> Token:
    """Cambia un refresh token válido por un token de acceso nuevo y un
    refresh token nuevo. El refresh token usado queda revocado (rotación):
    guarda siempre el último que devuelva la API."""
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


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Cerrar sesión")
def logout(payload: LogoutRequest, db: Annotated[Session, Depends(get_db)]) -> None:
    """Revoca el refresh token indicado. Responde `204` aunque el token ya no
    fuera válido. El token de acceso sigue funcionando hasta que caduca."""
    record = get_valid_refresh_token(db, payload.refresh_token)
    if record is not None:
        revoke_refresh_token(db, record)


@router.get(
    "/me", response_model=UserRead, summary="Ver el usuario autenticado", responses=AUTH_RESPONSES
)
def me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """Devuelve los datos del usuario dueño del token."""
    return current_user


@router.get(
    "/oauth/google/start",
    response_class=RedirectResponse,
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    summary="Empezar el login con Google",
    responses={
        307: {"description": "Redirección a la pantalla de consentimiento de Google."},
        **error_responses(
            503,
            e503=("Faltan las credenciales de Google OAuth en este entorno.",
                  "Login con Google no está configurado en este entorno"),
        ),
    },
)
def google_oauth_start() -> RedirectResponse:
    """Redirige al login de Google. Al terminar, Google vuelve a
    `GET /auth/oauth/google/callback`. Abrir en el navegador, no con
    `fetch`."""
    settings = get_settings()
    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Login con Google no está configurado en este entorno",
        )
    return RedirectResponse(google_oauth.build_authorize_url())


@router.get(
    "/oauth/google/callback",
    response_class=RedirectResponse,
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    summary="Completar el login con Google",
    responses={
        307: {
            "description": "Redirección al frontend (`/auth/social-callback`) con "
            "`access_token` y `refresh_token` en la query."
        },
        **error_responses(
            400,
            500,
            502,
            e400=("El `state` no es válido o ha caducado.", "state inválido o expirado"),
            e500=("No se pudo resolver el usuario.", "No se pudo resolver el usuario"),
            e502=("Google rechazó el código o no devolvió el email.",
                  "Google no devolvió sub/email"),
        ),
    },
)
async def google_oauth_callback(
    code: Annotated[str, Query(description="Código de autorización que envía Google.")],
    state: Annotated[str, Query(description="Valor anti-CSRF firmado por la API en el inicio.")],
    db: Annotated[Session, Depends(get_db)],
) -> RedirectResponse:
    """Lo llama Google, no el cliente. Intercambia el código por los datos
    del usuario, crea la cuenta si no existe (o liga Google a la cuenta con
    el mismo email) y redirige al frontend con los tokens."""
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
