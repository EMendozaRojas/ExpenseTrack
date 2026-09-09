from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

Kind = Literal["income", "expense"]


class CategoryCreate(BaseModel):
    name: str
    kind: Kind = "expense"
    parent_id: int | None = None
    icon: str | None = None
    color: str | None = None
    is_fixed: bool = False


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    owner_id: int | None
    parent_id: int | None
    kind: str
    icon: str | None
    color: str | None
    is_system: bool
    is_fixed: bool
    created_at: datetime
    children: list[CategoryRead] = []


class CategoryDeleteResult(BaseModel):
    reassigned_transactions: int
    reassigned_subcategories: int
