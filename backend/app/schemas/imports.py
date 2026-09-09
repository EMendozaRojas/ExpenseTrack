from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict

Classification = Literal["NEW", "EXACT_DUPLICATE", "PROBABLE_DUPLICATE"]
Strategy = Literal["append_new", "replace_range", "replace_selected"]


class ImportRowRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    posted_at: date
    amount: Decimal
    raw_description: str
    classification: Classification
    matched_transaction_id: int | None


class ImportPreview(BaseModel):
    id: int
    account_id: int
    filename: str
    status: str
    range_start: date
    range_end: date
    created_at: datetime
    new_count: int
    exact_duplicate_count: int
    probable_duplicate_count: int
    rows: list[ImportRowRead]


class ImportCommitRequest(BaseModel):
    strategy: Strategy = "append_new"
    row_ids: list[int] = []


class ImportCommitResult(BaseModel):
    id: int
    status: str
    strategy: Strategy
    inserted_count: int
    replaced_count: int
    skipped_count: int
