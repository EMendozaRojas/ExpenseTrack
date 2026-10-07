from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

Direction = Literal["income", "expense", "transfer"]

_AMOUNT = (
    "Importe con signo: negativo para gastos, positivo para ingresos. Nunca cero. Va en la "
    "moneda del movimiento (`currency`)."
)
_DIRECTION = "`expense` (gasto) o `income` (ingreso). Debe ser coherente con el signo de `amount`."
_CATEGORY = (
    "Subcategoría (no se admite una categoría raíz). Si se omite, se aplican las reglas de "
    "categorización y, si ninguna coincide, \"Sin Clasificar\"."
)
_COUNTERPARTY = "Comercio o persona con quien se hizo el movimiento."
_NOTE = "Nota libre."


class TransactionCreate(BaseModel):
    account_id: int = Field(description="Cuenta del movimiento.", examples=[1110])
    amount: Decimal = Field(description=_AMOUNT, examples=["-42.50"])
    direction: Literal["income", "expense"] = Field(description=_DIRECTION, examples=["expense"])
    posted_at: date = Field(description="Fecha del movimiento.", examples=["2026-10-07"])
    category_id: int | None = Field(default=None, description=_CATEGORY, examples=[95])
    counterparty: str | None = Field(
        default=None, description=_COUNTERPARTY, examples=["Mercadona"]
    )
    note: str | None = Field(default=None, description=_NOTE, examples=["Compra semanal"])
    currency: str | None = Field(
        default=None,
        description="Moneda del importe (código ISO 4217). Por defecto, la de la cuenta; si es "
        "otra, se convierte con el tipo de cambio de la fecha.",
        examples=["EUR"],
    )

    @model_validator(mode="after")
    def check_amount_sign(self) -> "TransactionCreate":
        if self.amount == 0:
            raise ValueError("amount no puede ser cero")
        if self.direction == "expense" and self.amount > 0:
            raise ValueError("un gasto debe tener importe negativo")
        if self.direction == "income" and self.amount < 0:
            raise ValueError("un ingreso debe tener importe positivo")
        return self


class TransactionUpdate(BaseModel):
    amount: Decimal = Field(description=_AMOUNT, examples=["-45.00"])
    direction: Literal["income", "expense"] = Field(description=_DIRECTION, examples=["expense"])
    posted_at: date = Field(description="Fecha del movimiento.", examples=["2026-10-07"])
    category_id: int | None = Field(
        default=None,
        description="Subcategoría. Si se omite, el movimiento pasa a \"Sin Clasificar\".",
        examples=[95],
    )
    counterparty: str | None = Field(
        default=None, description=_COUNTERPARTY, examples=["Mercadona"]
    )
    note: str | None = Field(default=None, description=_NOTE, examples=["Compra semanal"])

    @model_validator(mode="after")
    def check_amount_sign(self) -> "TransactionUpdate":
        if self.amount == 0:
            raise ValueError("amount no puede ser cero")
        if self.direction == "expense" and self.amount > 0:
            raise ValueError("un gasto debe tener importe negativo")
        if self.direction == "income" and self.amount < 0:
            raise ValueError("un ingreso debe tener importe positivo")
        return self


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Id del movimiento.")
    account_id: int = Field(description="Cuenta del movimiento.")
    owner_id: int = Field(description="Id del usuario dueño.")
    amount: Decimal = Field(
        description="Importe con signo en la moneda del movimiento: negativo = gasto o salida."
    )
    direction: str = Field(description="`income`, `expense` o `transfer`.")
    posted_at: date = Field(description="Fecha del movimiento.")
    category_id: int | None = Field(description="Subcategoría; `null` en las transferencias.")
    counterparty: str | None = Field(description=_COUNTERPARTY)
    raw_description: str | None = Field(
        description="Concepto original del extracto, en los movimientos importados."
    )
    note: str | None = Field(description=_NOTE)
    source: str = Field(description="Origen: `manual` o `import`.")
    currency: str = Field(description="Moneda del importe (código ISO 4217).")
    fx_rate_to_account_currency: Decimal | None = Field(
        description="Tipo de cambio aplicado si la moneda difiere de la de la cuenta."
    )
    amount_in_account_currency: Decimal | None = Field(
        description="Importe convertido a la moneda de la cuenta."
    )
    transfer_group_id: UUID | None = Field(
        description="Enlaza los dos lados de una transferencia."
    )
    created_at: datetime = Field(description="Fecha de alta.")
    updated_at: datetime = Field(description="Fecha de la última modificación.")


class TransactionPage(BaseModel):
    items: list[TransactionRead] = Field(description="Movimientos de esta página.")
    next_cursor: str | None = Field(
        description="Cursor para pedir la página siguiente; `null` si no hay más."
    )


class TransactionTrashRead(TransactionRead):
    deleted_at: datetime = Field(description="Cuándo se borró.")
    purge_at: datetime = Field(description="Cuándo se eliminará definitivamente (30 días después).")


class TransferCreate(BaseModel):
    from_account_id: int = Field(description="Cuenta de origen.", examples=[1110])
    to_account_id: int = Field(
        description="Cuenta de destino (distinta de la de origen).", examples=[2043]
    )
    amount: Decimal = Field(description="Importe a transferir, en positivo.", examples=["200.00"])
    posted_at: date = Field(description="Fecha de la transferencia.", examples=["2026-10-07"])
    note: str | None = Field(default=None, description=_NOTE, examples=["Ahorro del mes"])

    @model_validator(mode="after")
    def check_amount(self) -> "TransferCreate":
        if self.amount <= 0:
            raise ValueError("amount debe ser positivo")
        if self.from_account_id == self.to_account_id:
            raise ValueError("las cuentas de origen y destino deben ser distintas")
        return self


class CategorySummary(BaseModel):
    category_id: int | None = Field(description="Id de la categoría.")
    category_name: str | None = Field(description="Nombre de la categoría.")
    total: Decimal = Field(description="Gastado en el mes en esa categoría, en positivo.")


class MonthlySummary(BaseModel):
    year: int = Field(description="Año.")
    month: int = Field(description="Mes (1–12).")
    total: Decimal = Field(description="Total gastado en el mes, en positivo.")
    by_category: list[CategorySummary] = Field(
        description="Gasto por categoría, ordenado por nombre."
    )
