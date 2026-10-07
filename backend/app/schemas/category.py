from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Kind = Literal["income", "expense"]


class CategoryCreate(BaseModel):
    name: str = Field(description="Nombre de la categoría.", examples=["Gimnasio"])
    kind: Kind = Field(
        default="expense",
        description="`expense` (gasto) o `income` (ingreso). En una subcategoría se ignora: "
        "hereda el del padre.",
        examples=["expense"],
    )
    parent_id: int | None = Field(
        default=None,
        description="Categoría raíz de la que cuelga. Sin padre, se crea una raíz.",
        examples=[50],
    )
    icon: str | None = Field(default=None, description="Emoji o icono.", examples=["🏋️"])
    color: str | None = Field(
        default=None, description="Color en hexadecimal.", examples=["#4F86C6"]
    )
    is_fixed: bool = Field(
        default=False,
        description="Si es un gasto fijo (alquiler, suscripciones…). El dashboard separa "
        "fijos y variables.",
        examples=[True],
    )


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Id de la categoría.")
    name: str = Field(description="Nombre.")
    owner_id: int | None = Field(description="Usuario dueño; `null` en las de sistema.")
    parent_id: int | None = Field(description="Categoría raíz; `null` si es una raíz.")
    kind: str = Field(description="`expense` o `income`.")
    icon: str | None = Field(description="Emoji o icono.")
    color: str | None = Field(description="Color en hexadecimal.")
    is_system: bool = Field(description="Si es de sistema (común a todos y no se puede borrar).")
    is_fixed: bool = Field(description="Si es un gasto fijo.")
    created_at: datetime = Field(description="Fecha de creación.")
    children: list[CategoryRead] = Field(
        default=[], description="Subcategorías (solo en las raíces)."
    )


class CategoryDeleteResult(BaseModel):
    reassigned_transactions: int = Field(
        description="Movimientos que pasaron a \"Sin Clasificar\"."
    )
    reassigned_subcategories: int = Field(
        description="Subcategorías que subieron al nivel del padre."
    )
