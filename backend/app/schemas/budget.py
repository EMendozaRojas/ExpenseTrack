from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Status = Literal["ok", "warning", "exceeded"]
Source = Literal["series", "override", "single"]
Scope = Literal["this", "following"]
Flag = Literal["raise", "lower", "keep", "create"]


def _positive(value: Decimal) -> Decimal:
    if value <= 0:
        raise ValueError("amount debe ser mayor que cero")
    return value


class BudgetCreate(BaseModel):
    category_id: int
    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    amount: Decimal
    repeat: bool = True

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, value: Decimal) -> Decimal:
        return _positive(value)


class BudgetUpdate(BaseModel):
    amount: Decimal
    scope: Scope = "this"
    repeat: bool | None = None

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, value: Decimal) -> Decimal:
        return _positive(value)


class BudgetPace(BaseModel):
    projected: Decimal
    will_exceed: bool


class BudgetStatus(BaseModel):
    category_id: int | None
    category_name: str
    category_icon: str | None
    month: str
    amount: Decimal
    repeats: bool
    source: Source
    editable: bool
    spent: Decimal
    pct: float
    status: Status
    pace: BudgetPace | None


class PlannedMonthRead(BaseModel):
    month: str
    amount: Decimal
    kind: Literal["override", "single", "series"]


class CopyPreviewItem(BaseModel):
    category_id: int
    category_name: str
    amount: Decimal


class CopyItem(BaseModel):
    category_id: int
    amount: Decimal

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, value: Decimal) -> Decimal:
        return _positive(value)


class CopyRequest(BaseModel):
    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    items: list[CopyItem]


class CopyResult(BaseModel):
    created: list[int]
    skipped: list[int]


class MonthlySpent(BaseModel):
    month: str
    spent: Decimal


class RecommendationBasis(BaseModel):
    months: list[MonthlySpent]
    mean: Decimal
    same_month_last_year: Decimal | None
    share_pct: float | None
    over_typical: bool | None


class BudgetRecommendation(BaseModel):
    category_id: int
    category_name: str
    parent_id: int | None
    flag: Flag
    suggested_amount: Decimal
    current_amount: Decimal | None
    basis: RecommendationBasis
