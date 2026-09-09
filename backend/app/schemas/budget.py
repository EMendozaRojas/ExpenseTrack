from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

Status = Literal["ok", "warning", "exceeded"]


class BudgetCreate(BaseModel):
    category_id: int
    amount: Decimal

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("amount debe ser mayor que cero")
        return value


class BudgetUpdate(BaseModel):
    amount: Decimal | None = None
    is_active: bool | None = None

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and value <= 0:
            raise ValueError("amount debe ser mayor que cero")
        return value


class BudgetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    category_name: str
    amount: Decimal
    is_active: bool
    created_at: datetime


class BudgetStatus(BaseModel):
    id: int
    category_id: int
    category_name: str
    category_icon: str | None
    amount: Decimal
    is_active: bool
    spent: Decimal
    pct: float
    status: Status
