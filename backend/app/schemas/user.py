from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, computed_field, field_validator


class UserCreate(BaseModel):
    email: EmailStr = Field(
        description="Email con el que se iniciará sesión.", examples=["ana@example.com"]
    )
    password: str = Field(description="Contraseña.", examples=["una-contraseña-segura"])


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
