from pydantic import BaseModel, ConfigDict, field_validator


class UserPreferencesRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    base_currency: str
    locale: str


class UserPreferencesUpdate(BaseModel):
    base_currency: str | None = None
    locale: str | None = None

    @field_validator("base_currency")
    @classmethod
    def currency_must_be_iso_code(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip().upper()
        if len(value) != 3 or not value.isalpha():
            raise ValueError("base_currency debe ser un código ISO 4217 de 3 letras")
        return value
