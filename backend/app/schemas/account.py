from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

AccountType = Literal["checking", "savings", "credit_card", "cash", "wallet"]


class AccountCreate(BaseModel):
    name: str
    type: AccountType
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    initial_balance: Decimal = Decimal("0")


class AccountUpdate(BaseModel):
    name: str | None = None
    type: AccountType | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=3)


class AccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    name: str
    type: str
    currency: str
    initial_balance: Decimal
    balance: Decimal
    is_archived: bool
    created_at: datetime
    updated_at: datetime
