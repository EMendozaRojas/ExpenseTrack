"""Flujo OAuth2 con Google (authorization code), sin dependencias tipo
authlib: solo `httpx` contra los endpoints públicos de Google.

El `state` es un JWT de corta duración firmado con la misma clave que los
access tokens, para no necesitar sesión de servidor (protección CSRF sin
estado). Nada de esto se ejecuta en los tests unitarios salvo con Google
mockeado: probar el flujo real requiere GOOGLE_CLIENT_ID/SECRET válidos.
"""

from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx
import jwt

from app.core.config import get_settings

AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
STATE_PURPOSE = "oauth_state"
STATE_TTL_MINUTES = 5


class OAuthError(Exception):
    pass


def create_state() -> str:
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(minutes=STATE_TTL_MINUTES)
    payload = {"purpose": STATE_PURPOSE, "exp": expire}
    return str(jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm))


def verify_state(state: str) -> bool:
    settings = get_settings()
    try:
        payload = jwt.decode(state, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        return False
    return bool(payload.get("purpose") == STATE_PURPOSE)


def build_authorize_url() -> str:
    settings = get_settings()
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": create_state(),
        "access_type": "online",
        "prompt": "select_account",
    }
    return f"{AUTHORIZE_URL}?{urlencode(params)}"


async def exchange_code_for_userinfo(code: str) -> dict[str, Any]:
    """Intercambia el `code` por tokens y devuelve el userinfo de Google
    (`sub`, `email`, ...). Lanza `OAuthError` si algo falla."""
    settings = get_settings()
    async with httpx.AsyncClient(timeout=10.0) as client:
        token_response = await client.post(
            TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_response.status_code != 200:
            raise OAuthError(f"Google rechazó el intercambio de código: {token_response.text}")
        access_token = token_response.json().get("access_token")
        if not access_token:
            raise OAuthError("Google no devolvió un access_token")

        userinfo_response = await client.get(
            USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"}
        )
        if userinfo_response.status_code != 200:
            raise OAuthError(f"No se pudo obtener el perfil de Google: {userinfo_response.text}")
        return dict(userinfo_response.json())
