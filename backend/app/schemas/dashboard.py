from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.transaction import CategorySummary

NetStatus = Literal["a_favor", "en_contra"]


class DashboardCategoryNode(BaseModel):
    category_id: int = Field(description="Categoría raíz.")
    category_name: str = Field(description="Nombre de la categoría raíz.")
    icon: str | None = Field(description="Icono de la categoría.")
    color: str | None = Field(description="Color de la categoría.")
    total: Decimal = Field(description="Gastado en la categoría y sus subcategorías.")
    subcategories: list[CategorySummary] = Field(
        description="Gasto por subcategoría, de mayor a menor."
    )


class DashboardSummary(BaseModel):
    year: int = Field(description="Año.")
    month: int = Field(description="Mes (1–12).")
    income_total: Decimal = Field(description="Total de ingresos.")
    expense_total: Decimal = Field(description="Total de gastos, en positivo.")
    net_total: Decimal = Field(description="Ingresos menos gastos.")
    net_status: NetStatus = Field(
        description="`a_favor` si el neto es 0 o positivo, `en_contra` si es negativo."
    )
    fixed_total: Decimal = Field(description="Gasto en subcategorías marcadas como fijas.")
    variable_total: Decimal = Field(description="Resto del gasto.")
    by_category: list[DashboardCategoryNode] = Field(
        description="Gasto por categoría raíz, de mayor a menor."
    )
    incomplete_data: bool = Field(
        description="Solo en el mes en curso: si no hay movimientos en los últimos 3 días."
    )
    last_transaction_date: date | None = Field(
        description="Fecha del último ingreso o gasto del mes."
    )
