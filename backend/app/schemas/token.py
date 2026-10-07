from pydantic import BaseModel, Field

_REFRESH_TOKEN_EXAMPLE = "Yk3mQ2v9pXr7TfA1cW0sLdE8uNhB4oJz"


class Token(BaseModel):
    access_token: str = Field(
        description="Token de acceso (JWT). Se envía como `Authorization: Bearer <token>`. "
        "Caduca a los 60 minutos (por defecto; configurable)."
    )
    token_type: str = Field(default="bearer", description="Siempre `bearer`.")
    refresh_token: str | None = Field(
        default=None,
        description="Token para pedir un token de acceso nuevo con `POST /auth/refresh`. "
        "Caduca a los 30 días (por defecto; configurable) y se revoca al usarlo.",
    )


class RefreshRequest(BaseModel):
    refresh_token: str = Field(
        description="Refresh token devuelto por el login o por la última renovación.",
        examples=[_REFRESH_TOKEN_EXAMPLE],
    )


class LogoutRequest(BaseModel):
    refresh_token: str = Field(
        description="Refresh token que se quiere revocar.", examples=[_REFRESH_TOKEN_EXAMPLE]
    )


class TokenPayload(BaseModel):
    sub: str | None = None
