from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

MatchType = Literal["contains", "starts_with"]


_MATCH_TYPE = "`contains` (contiene el patrón) o `starts_with` (empieza por el patrón)."
_PATTERN = "Texto a buscar en la contraparte, la descripción original o la nota."
_PRIORITY = "Prioridad: con varias reglas que coinciden, gana la de mayor prioridad."


class CategorizationRuleCreate(BaseModel):
    match_type: MatchType = Field(
        default="contains", description=_MATCH_TYPE, examples=["contains"]
    )
    pattern: str = Field(max_length=255, description=_PATTERN, examples=["mercadona"])
    category_id: int = Field(description="Subcategoría que se asigna.", examples=[95])
    priority: int = Field(default=0, description=_PRIORITY, examples=[10])
    is_enabled: bool = Field(default=True, description="Si la regla está activa.", examples=[True])


class CategorizationRuleUpdate(BaseModel):
    match_type: MatchType | None = Field(
        default=None, description=_MATCH_TYPE, examples=["starts_with"]
    )
    pattern: str | None = Field(
        max_length=255, default=None, description=_PATTERN, examples=["lidl"]
    )
    category_id: int | None = Field(
        default=None, description="Subcategoría que se asigna.", examples=[95]
    )
    priority: int | None = Field(default=None, description=_PRIORITY, examples=[5])
    is_enabled: bool | None = Field(
        default=None, description="Activar o desactivar la regla.", examples=[False]
    )


class CategorizationRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Id de la regla.")
    owner_id: int | None = Field(description="Usuario dueño; `null` en las de sistema.")
    match_type: str = Field(description=_MATCH_TYPE)
    pattern: str = Field(description=_PATTERN)
    category_id: int = Field(description="Subcategoría que se asigna.")
    priority: int = Field(description=_PRIORITY)
    is_enabled: bool = Field(description="Si la regla está activa.")
    created_at: datetime = Field(description="Fecha de creación.")


class RulePreviewResult(BaseModel):
    matching_count: int = Field(description="Movimientos que coincidirían con el patrón.")


class RuleApplyResult(BaseModel):
    updated_count: int = Field(description="Movimientos que se recategorizaron.")


class BulkCategorizeRequest(BaseModel):
    transaction_ids: list[int] = Field(
        description="Movimientos a recategorizar.", examples=[[3233, 3234]]
    )
    category_id: int = Field(description="Subcategoría que se les asigna.", examples=[95])


class BulkCategorizeResult(BaseModel):
    updated_count: int = Field(description="Cuántos movimientos cambiaron.")
