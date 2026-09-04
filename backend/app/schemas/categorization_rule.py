from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

MatchType = Literal["contains", "starts_with"]


class CategorizationRuleCreate(BaseModel):
    match_type: MatchType = "contains"
    pattern: str
    category_id: int
    priority: int = 0
    is_enabled: bool = True


class CategorizationRuleUpdate(BaseModel):
    match_type: MatchType | None = None
    pattern: str | None = None
    category_id: int | None = None
    priority: int | None = None
    is_enabled: bool | None = None


class CategorizationRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int | None
    match_type: str
    pattern: str
    category_id: int
    priority: int
    is_enabled: bool
    created_at: datetime


class RulePreviewResult(BaseModel):
    matching_count: int


class RuleApplyResult(BaseModel):
    updated_count: int


class BulkCategorizeRequest(BaseModel):
    transaction_ids: list[int]
    category_id: int


class BulkCategorizeResult(BaseModel):
    updated_count: int
