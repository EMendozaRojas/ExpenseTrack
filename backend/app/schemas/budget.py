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
    category_id: int = Field(
        description="Categoría de gasto, raíz o subcategoría.", examples=[95]
    )
    year: int = Field(ge=2000, le=2100, description="Año del primer mes.", examples=[2026])
    month: int = Field(
        ge=1, le=12, description="Primer mes (1–12): el actual o uno futuro.", examples=[10]
    )
    amount: Decimal = Field(
        description="Tope mensual, mayor que cero, en la moneda base.", examples=["300.00"]
    )
    repeat: bool = Field(
        default=True,
        description="Si el monto se repite cada mes (por defecto) o solo aplica a este mes.",
        examples=[True],
    )

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, value: Decimal) -> Decimal:
        return _positive(value)


class BudgetUpdate(BaseModel):
    amount: Decimal = Field(description="Nuevo tope, mayor que cero.", examples=["350.00"])
    scope: Scope = Field(
        default="this",
        description="Si se repite: `this` (solo este mes) o `following` (este mes y los "
        "siguientes, conservando los meses con monto propio).",
        examples=["following"],
    )
    repeat: bool | None = Field(
        default=None,
        description="`false`: deja de repetirse después de este mes. `true`: empieza a "
        "repetirse desde este mes. Si se omite, no cambia.",
        examples=[None],
    )

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, value: Decimal) -> Decimal:
        return _positive(value)


class BudgetPace(BaseModel):
    projected: Decimal = Field(
        description="Gasto previsto a final de mes: gasto / días transcurridos × días del mes."
    )
    will_exceed: bool = Field(description="Si al ritmo actual se llegará al tope.")


class BudgetStatus(BaseModel):
    category_id: int | None = Field(
        description="Categoría; `null` en meses conservados de una categoría borrada."
    )
    category_name: str = Field(description="Nombre de la categoría.")
    category_icon: str | None = Field(description="Icono de la categoría.")
    month: str = Field(description="Mes, `YYYY-MM`.")
    amount: Decimal = Field(description="Tope de ese mes.")
    repeats: bool = Field(description="Si el mes forma parte de un presupuesto que se repite.")
    source: Source = Field(
        description="`series` (monto de la serie), `override` (monto propio de ese mes dentro "
        "de una serie) o `single` (presupuesto de un solo mes)."
    )
    editable: bool = Field(description="Si se puede editar o borrar (mes actual o futuro).")
    spent: Decimal = Field(description="Gastado en ese mes, en positivo.")
    pct: float = Field(description="`spent / amount × 100`, con un decimal; puede pasar de 100.")
    status: Status = Field(
        description="`ok` (menos del 80%), `warning` (80% a 100%) o `exceeded` (100% o más)."
    )
    pace: BudgetPace | None = Field(
        description="Ritmo de gasto; solo en el mes en curso a partir del sexto día."
    )


class PlannedMonthRead(BaseModel):
    month: str = Field(description="Mes, `YYYY-MM`.")
    amount: Decimal = Field(description="Monto planificado.")
    kind: Literal["override", "single", "series"] = Field(
        description="`override` (monto propio dentro de la serie), `single` (mes suelto) o "
        "`series` (empieza otra serie con ese monto)."
    )


class CopyPreviewItem(BaseModel):
    category_id: int = Field(description="Categoría.")
    category_name: str = Field(description="Nombre de la categoría.")
    amount: Decimal = Field(description="Monto que tenía en el mes anterior.")


class CopyItem(BaseModel):
    category_id: int = Field(description="Categoría a copiar.", examples=[98])
    amount: Decimal = Field(description="Monto para el nuevo mes.", examples=["150.00"])

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, value: Decimal) -> Decimal:
        return _positive(value)


class CopyRequest(BaseModel):
    year: int = Field(ge=2000, le=2100, description="Año del mes destino.", examples=[2026])
    month: int = Field(
        ge=1, le=12, description="Mes destino (1–12): el actual o uno futuro.", examples=[11]
    )
    items: list[CopyItem] = Field(
        description="Presupuestos a crear.",
        examples=[[{"category_id": 98, "amount": "150.00"}]],
    )


class CopyResult(BaseModel):
    created: list[int] = Field(description="Categorías en las que se creó el presupuesto.")
    skipped: list[int] = Field(
        description="Categorías omitidas porque ya tenían presupuesto en ese mes."
    )


class MonthlySpent(BaseModel):
    month: str = Field(description="Mes, `YYYY-MM`.")
    spent: Decimal = Field(description="Gastado en ese mes.")


class RecommendationBasis(BaseModel):
    months: list[MonthlySpent] = Field(description="Gasto de los 3 meses de la ventana.")
    mean: Decimal = Field(description="Media de los meses con gasto.")
    same_month_last_year: Decimal | None = Field(
        description="Gastado en el mismo mes del año anterior; `null` si no hubo. Informativo."
    )
    share_pct: float | None = Field(
        description="Porcentaje del gasto total que supuso la categoría (solo en raíces de "
        "sistema)."
    )
    over_typical: bool | None = Field(
        description="Si ese porcentaje supera lo habitual para la categoría (Vivienda 35%, "
        "Transporte 20%, Alimentación 15%); `null` si no hay referencia."
    )


class BudgetRecommendation(BaseModel):
    category_id: int = Field(description="Categoría.")
    category_name: str = Field(description="Nombre de la categoría.")
    parent_id: int | None = Field(description="Categoría raíz; `null` si es una raíz.")
    flag: Flag = Field(description="`raise`, `lower`, `keep` o `create`.")
    suggested_amount: Decimal = Field(description="Tope sugerido (media redondeada).")
    current_amount: Decimal | None = Field(
        description="Tope actual en el mes en curso; `null` si no tiene presupuesto."
    )
    basis: RecommendationBasis = Field(description="Datos con los que se calculó.")
