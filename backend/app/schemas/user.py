from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, computed_field, field_validator


def normalize_email(value: str) -> str:
    """Los emails se guardan y se comparan sin espacios y en minúsculas."""
    return value.strip().lower()


class UserCreate(BaseModel):
    email: EmailStr = Field(
        max_length=255,
        description="Email con el que se iniciará sesión. Se guarda en minúsculas.",
        examples=["ana@example.com"],
    )
    password: str = Field(
        min_length=8,
        max_length=72,
        description="Contraseña, de 8 a 72 caracteres.",
        examples=["una-contraseña-segura"],
    )

    @field_validator("email", mode="before")
    @classmethod
    def email_normalized(cls, value: object) -> object:
        return normalize_email(value) if isinstance(value, str) else value


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Identificador del usuario.")
    email: EmailStr = Field(description="Email del usuario.")
    full_name: str | None = Field(
        description="Nombre que se muestra en la app; `null` hasta completar el onboarding."
    )
    created_at: datetime = Field(description="Fecha de alta.")
    avatar_storage_key: str | None = Field(default=None, exclude=True)

    @computed_field(  # type: ignore[prop-decorator]
        description="Si el usuario tiene foto de perfil (`GET /users/me/avatar`)."
    )
    @property
    def has_avatar(self) -> bool:
        return self.avatar_storage_key is not None


class UserProfileUpdate(BaseModel):
    full_name: str | None = Field(
        max_length=120,
        default=None,
        description="Nombre que se muestra en la app. No puede quedar vacío.",
        examples=["Ana García"],
    )

    @field_validator("full_name")
    @classmethod
    def name_not_blank(cls, value: str | None) -> str | None:
        if value is not None:
            value = value.strip()
            if not value:
                raise ValueError("El nombre no puede estar vacío")
        return value
