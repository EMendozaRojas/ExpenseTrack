from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserPreferencesRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    base_currency: str = Field(
        description="Moneda base del usuario (código ISO 4217). Es la moneda de presupuestos, "
        "metas y totales."
    )
    locale: str = Field(description="Idioma y región para formatear fechas e importes.")
    has_transactions: bool = Field(
        description="Si el usuario ya tiene movimientos; en ese caso la moneda base no se "
        "puede cambiar."
    )


class UserPreferencesUpdate(BaseModel):
    base_currency: str | None = Field(
        default=None,
        description="Nueva moneda base (código ISO 4217 de 3 letras; se pasa a mayúsculas).",
        examples=["EUR"],
    )
    locale: str | None = Field(
        default=None, description="Nuevo idioma y región.", examples=["es-ES"]
    )

    @field_validator("base_currency")
    @classmethod
    def currency_must_be_iso_code(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip().upper()
        if len(value) != 3 or not value.isalpha():
            raise ValueError("base_currency debe ser un código ISO 4217 de 3 letras")
        return value
