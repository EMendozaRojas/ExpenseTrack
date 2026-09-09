from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

from app.schemas.transaction import CategorySummary

NetStatus = Literal["a_favor", "en_contra"]


class DashboardCategoryNode(BaseModel):
    category_id: int
    category_name: str
    icon: str | None
    color: str | None
    total: Decimal
    subcategories: list[CategorySummary]


class DashboardSummary(BaseModel):
    year: int
    month: int
    income_total: Decimal
    expense_total: Decimal
    net_total: Decimal
    net_status: NetStatus
    fixed_total: Decimal
    variable_total: Decimal
    by_category: list[DashboardCategoryNode]
    incomplete_data: bool
    last_transaction_date: date | None
