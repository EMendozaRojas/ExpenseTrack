from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator


class RecurringSeriesRead(BaseModel):
    key: str
    label: str
    direction: str
    category_id: int | None
    category_name: str | None
    occurrences: int
    avg_amount: Decimal
    cadence_days: float
    cadence_label: str
    first_posted_at: date
    last_posted_at: date
    dismissed: bool


class DismissRequest(BaseModel):
    series_key: str


class AntSpendingGroup(BaseModel):
    category_id: int
    category_name: str
    occurrences: int
    aggregate: Decimal
    avg_amount: Decimal


class InsightSettingsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ant_max_amount: Decimal
    ant_min_occurrences: int
    ant_min_aggregate: Decimal


class InsightSettingsUpdate(BaseModel):
    ant_max_amount: Decimal | None = None
    ant_min_occurrences: int | None = None
    ant_min_aggregate: Decimal | None = None

    @field_validator("ant_max_amount", "ant_min_aggregate")
    @classmethod
    def amounts_must_be_positive(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and value <= 0:
            raise ValueError("debe ser mayor que cero")
        return value

    @field_validator("ant_min_occurrences")
    @classmethod
    def occurrences_must_be_positive(cls, value: int | None) -> int | None:
        if value is not None and value < 1:
            raise ValueError("debe ser al menos 1")
        return value
