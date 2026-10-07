from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Id de la notificación.")
    type: str = Field(
        description="`budget_warning` (presupuesto al 80%), `budget_exceeded` (al 100%), "
        "`budget_month_summary` (resumen de cierre de mes), `budget_category_deleted` "
        "(presupuesto de una categoría borrada), `goal_near` (meta al 80%) o `goal_reached` "
        "(meta alcanzada)."
    )
    title: str = Field(description="Título.")
    body: str = Field(description="Texto completo.")
    related_id: int = Field(
        description="Elemento relacionado: la categoría en los avisos de presupuesto, la meta "
        "en los de metas, 0 en el resumen de cierre."
    )
    is_read: bool = Field(description="Si ya se leyó.")
    created_at: datetime = Field(description="Cuándo se creó.")


class UnreadCount(BaseModel):
    count: int = Field(description="Notificaciones sin leer.")
