from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FxRateCreate(BaseModel):
    rate_date: date = Field(description="Día al que corresponde.", examples=["2026-10-07"])
    base: str = Field(
        description="Moneda de origen (código ISO 4217; se pasa a mayúsculas).", examples=["USD"]
    )
    quote: str = Field(description="Moneda de destino (código ISO 4217).", examples=["EUR"])
    rate: Decimal = Field(
        description="Unidades de `quote` por una unidad de `base`. Mayor que cero.",
        examples=["0.9215"],
    )

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

    id: int = Field(description="Id del tipo de cambio.")
    rate_date: date = Field(description="Día al que corresponde.")
    base: str = Field(description="Moneda de origen.")
    quote: str = Field(description="Moneda de destino.")
    rate: Decimal = Field(description="Unidades de `quote` por una unidad de `base`.")
