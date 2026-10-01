from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator

Direction = Literal["income", "expense", "transfer"]


class TransactionCreate(BaseModel):
    account_id: int
    amount: Decimal
    direction: Literal["income", "expense"]
    posted_at: date
    category_id: int | None = None
    counterparty: str | None = None
    note: str | None = None
    currency: str | None = None

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
    amount: Decimal
    direction: Literal["income", "expense"]
    posted_at: date
    category_id: int | None = None
    counterparty: str | None = None
    note: str | None = None

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

    id: int
    account_id: int
    owner_id: int
    amount: Decimal
    direction: str
    posted_at: date
    category_id: int | None
    counterparty: str | None
    raw_description: str | None
    note: str | None
    source: str
    currency: str
    fx_rate_to_account_currency: Decimal | None
    amount_in_account_currency: Decimal | None
    transfer_group_id: UUID | None
    created_at: datetime
    updated_at: datetime


class TransactionPage(BaseModel):
    items: list[TransactionRead]
    next_cursor: str | None


class TransactionTrashRead(TransactionRead):
    deleted_at: datetime
    purge_at: datetime


class TransferCreate(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: Decimal
    posted_at: date
    note: str | None = None

    @model_validator(mode="after")
    def check_amount(self) -> "TransferCreate":
        if self.amount <= 0:
            raise ValueError("amount debe ser positivo")
        if self.from_account_id == self.to_account_id:
            raise ValueError("las cuentas de origen y destino deben ser distintas")
        return self


class CategorySummary(BaseModel):
    category_id: int | None
    category_name: str | None
    total: Decimal


class MonthlySummary(BaseModel):
    year: int
    month: int
    total: Decimal
    by_category: list[CategorySummary]
