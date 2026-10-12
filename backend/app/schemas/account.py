from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.limits import MAX_AMOUNT

AccountType = Literal["general", "checking", "savings", "credit_card", "cash", "wallet"]


_TYPE_DESCRIPTION = (
    "Tipo de cuenta: `general` (sin especificar), `checking` (corriente), `savings` (ahorro), "
    "`credit_card` (tarjeta de crédito), `cash` (efectivo) o `wallet` (monedero digital)."
)


class AccountCreate(BaseModel):
    name: str = Field(
        max_length=120, description="Nombre de la cuenta.", examples=["Cuenta Principal"]
    )
    type: AccountType = Field(
        default="general",
        description=_TYPE_DESCRIPTION + " Opcional; por defecto `general`.",
        examples=["general"],
    )
    currency: str = Field(
        default="EUR",
        min_length=3,
        max_length=3,
        description="Moneda de la cuenta (código ISO 4217; se pasa a mayúsculas).",
        examples=["EUR"],
    )
    initial_balance: Decimal = Field(
        gt=-MAX_AMOUNT,
        lt=MAX_AMOUNT,
        default=Decimal("0"),
        description="Saldo al crear la cuenta, antes de cualquier movimiento.",
        examples=["1500.00"],
    )
    is_primary: bool = Field(
        default=False,
        description="Si es la cuenta principal. Al marcarla, las demás dejan de serlo.",
        examples=[True],
    )


class AccountUpdate(BaseModel):
    name: str | None = Field(
        max_length=120, default=None, description="Nuevo nombre.", examples=["Ahorros"]
    )
    type: AccountType | None = Field(
        default=None, description=_TYPE_DESCRIPTION, examples=["savings"]
    )
    currency: str | None = Field(
        default=None,
        min_length=3,
        max_length=3,
        description="Nueva moneda (código ISO 4217).",
        examples=["USD"],
    )
    is_primary: bool | None = Field(
        default=None,
        description="Marcar o desmarcar como principal. Al marcarla, las demás dejan de serlo.",
        examples=[True],
    )


class AccountBalance(BaseModel):
    balance: Decimal = Field(description="Saldo actual de la cuenta, en su moneda.")


class AccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Id de la cuenta.")
    owner_id: int = Field(description="Id del usuario dueño.")
    name: str = Field(description="Nombre de la cuenta.")
    type: str = Field(description=_TYPE_DESCRIPTION)
    currency: str = Field(description="Moneda de la cuenta (código ISO 4217).")
    initial_balance: Decimal = Field(description="Saldo al crear la cuenta.")
    balance: Decimal = Field(
        description="Saldo actual: saldo inicial más los movimientos no borrados."
    )
    is_archived: bool = Field(description="Si la cuenta está archivada.")
    is_primary: bool = Field(description="Si es la cuenta principal del usuario.")
    created_at: datetime = Field(description="Fecha de creación.")
    updated_at: datetime = Field(description="Fecha de la última modificación.")
