from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator


class FxRateCreate(BaseModel):
    rate_date: date
    base: str
    quote: str
    rate: Decimal

    @field_validator("base", "quote")
    @classmethod
    def currency_must_be_iso_code(cls, value: str) -> str:
        value = value.strip().upper()
        if len(value) != 3 or not value.isalpha():
            raise ValueError("debe ser un código ISO 4217 de 3 letras")
        return value

    @field_validator("rate")
    @classmethod
    def rate_must_be_positive(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("rate debe ser mayor que cero")
        return value


class FxRateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rate_date: date
    base: str
    quote: str
    rate: Decimal
