from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, field_validator

Status = Literal["active", "completed", "archived"]


class GoalCreate(BaseModel):
    name: str
    target_amount: Decimal
    target_date: date | None = None
    linked_account_id: int | None = None

    @field_validator("target_amount")
    @classmethod
    def target_amount_must_be_positive(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("target_amount debe ser mayor que cero")
        return value

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("name no puede estar vacío")
        return value.strip()


class GoalUpdate(BaseModel):
    name: str | None = None
    target_amount: Decimal | None = None
    target_date: date | None = None
    linked_account_id: int | None = None
    status: Status | None = None

    @field_validator("target_amount")
    @classmethod
    def target_amount_must_be_positive(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and value <= 0:
            raise ValueError("target_amount debe ser mayor que cero")
        return value


class GoalRead(BaseModel):
    id: int
    name: str
    target_amount: Decimal
    target_date: date | None
    linked_account_id: int | None
    status: Status
    current_amount: Decimal
    pct: float
    created_at: datetime


class ContributionCreate(BaseModel):
    amount: Decimal
    contributed_at: date
    note: str | None = None

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("amount debe ser mayor que cero")
        return value


class ContributionRead(BaseModel):
    id: int
    goal_id: int
    amount: Decimal
    contributed_at: date
    note: str | None
    created_at: datetime


class GoalProjection(BaseModel):
    has_enough_data: bool
    monthly_pace: Decimal
    months_remaining: int | None
    projected_date: date | None
