from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.limits import MAX_AMOUNT

_ANT_MAX = "Importe máximo de un gasto para contar como gasto hormiga."
_ANT_MIN_OCCURRENCES = "Mínimo de gastos en el mes para que una subcategoría aparezca."
_ANT_MIN_AGGREGATE = "Mínimo que deben sumar en el mes."


class RecurringSeriesRead(BaseModel):
    key: str = Field(description="Identificador estable de la serie (para descartarla).")
    label: str = Field(description="Contraparte o descripción que la identifica.")
    direction: str = Field(description="`income` o `expense`.")
    category_id: int | None = Field(description="Categoría del último movimiento de la serie.")
    category_name: str | None = Field(description="Nombre de esa categoría.")
    occurrences: int = Field(description="Número de movimientos de la serie.")
    avg_amount: Decimal = Field(description="Importe medio.")
    cadence_days: float = Field(description="Días medios entre ocurrencias.")
    cadence_label: str = Field(
        description="Cadencia: `semanal`, `quincenal`, `mensual`, `trimestral` o `irregular`."
    )
    first_posted_at: date = Field(description="Primera ocurrencia en la ventana.")
    last_posted_at: date = Field(description="Última ocurrencia.")
    dismissed: bool = Field(description="Si el usuario la descartó.")


class DismissRequest(BaseModel):
    series_key: str = Field(
        max_length=300,
        description="`key` de la serie (de `GET /insights/recurring`).",
        examples=["expense:NETFLIX"],
    )


class AntSpendingGroup(BaseModel):
    category_id: int = Field(description="Subcategoría.")
    category_name: str = Field(description="Nombre de la subcategoría.")
    occurrences: int = Field(description="Gastos pequeños en el mes.")
    aggregate: Decimal = Field(description="Suma de esos gastos.")
    avg_amount: Decimal = Field(description="Importe medio.")


class InsightSettingsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ant_max_amount: Decimal = Field(description=_ANT_MAX)
    ant_min_occurrences: int = Field(description=_ANT_MIN_OCCURRENCES)
    ant_min_aggregate: Decimal = Field(description=_ANT_MIN_AGGREGATE)


class InsightSettingsUpdate(BaseModel):
    ant_max_amount: Decimal | None = Field(
        lt=MAX_AMOUNT, default=None, description=_ANT_MAX + " Mayor que cero.", examples=["5.00"]
    )
    ant_min_occurrences: int | None = Field(
        default=None, description=_ANT_MIN_OCCURRENCES + " Al menos 1.", examples=[4]
    )
    ant_min_aggregate: Decimal | None = Field(
        lt=MAX_AMOUNT,
        default=None,
        description=_ANT_MIN_AGGREGATE + " Mayor que cero.",
        examples=["20.00"],
    )

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
