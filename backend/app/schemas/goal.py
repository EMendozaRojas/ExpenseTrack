from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Status = Literal["active", "completed", "archived"]


_LINKED_ACCOUNT = "Cuenta asociada, solo informativa: no se usa para calcular el progreso."


class GoalCreate(BaseModel):
    name: str = Field(description="Nombre de la meta.", examples=["Fondo de emergencia"])
    target_amount: Decimal = Field(
        description="Importe objetivo, mayor que cero, en la moneda base.", examples=["6000.00"]
    )
    target_date: date | None = Field(
        default=None, description="Fecha objetivo (opcional).", examples=["2027-06-30"]
    )
    linked_account_id: int | None = Field(
        default=None, description=_LINKED_ACCOUNT, examples=[2043]
    )

    @field_validator("target_amount")
    @classmethod
    def target_amount_must_be_positive(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("target_amount debe ser mayor que cero")
        return value

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("name no puede estar vacío")
        return value.strip()


class GoalUpdate(BaseModel):
    name: str | None = Field(default=None, description="Nuevo nombre.", examples=["Viaje a Japón"])
    target_amount: Decimal | None = Field(
        default=None, description="Nuevo importe objetivo, mayor que cero.", examples=["8000.00"]
    )
    target_date: date | None = Field(
        default=None, description="Nueva fecha objetivo.", examples=["2027-12-31"]
    )
    linked_account_id: int | None = Field(
        default=None, description=_LINKED_ACCOUNT, examples=[2043]
    )
    status: Status | None = Field(
        default=None,
        description="`active`, `completed` o `archived`.",
        examples=["archived"],
    )

    @field_validator("target_amount")
    @classmethod
    def target_amount_must_be_positive(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and value <= 0:
            raise ValueError("target_amount debe ser mayor que cero")
        return value


class GoalRead(BaseModel):
    id: int = Field(description="Id de la meta.")
    name: str = Field(description="Nombre.")
    target_amount: Decimal = Field(description="Importe objetivo.")
    target_date: date | None = Field(description="Fecha objetivo, si tiene.")
    linked_account_id: int | None = Field(description=_LINKED_ACCOUNT)
    status: Status = Field(
        description="`active`, `completed` (se alcanzó el objetivo) o `archived`."
    )
    current_amount: Decimal = Field(description="Suma de las aportaciones.")
    pct: float = Field(description="Avance en porcentaje (puede pasar de 100).")
    created_at: datetime = Field(description="Fecha de creación.")


class ContributionCreate(BaseModel):
    amount: Decimal = Field(description="Importe aportado, mayor que cero.", examples=["250.00"])
    contributed_at: date = Field(description="Fecha de la aportación.", examples=["2026-10-07"])
    note: str | None = Field(default=None, description="Nota libre.", examples=["Paga extra"])

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("amount debe ser mayor que cero")
        return value


class ContributionRead(BaseModel):
    id: int = Field(description="Id de la aportación.")
    goal_id: int = Field(description="Meta a la que pertenece.")
    amount: Decimal = Field(description="Importe aportado.")
    contributed_at: date = Field(description="Fecha de la aportación.")
    note: str | None = Field(description="Nota libre.")
    created_at: datetime = Field(description="Fecha de registro.")


class GoalProjection(BaseModel):
    has_enough_data: bool = Field(
        description="Si hay ritmo suficiente para estimar (o la meta ya se alcanzó)."
    )
    monthly_pace: Decimal = Field(description="Media mensual aportada en la ventana.")
    months_remaining: int | None = Field(
        description="Meses que faltan al ritmo actual; `null` sin datos suficientes."
    )
    projected_date: date | None = Field(
        description="Fecha estimada; `null` sin datos suficientes."
    )
