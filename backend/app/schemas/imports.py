from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Classification = Literal["NEW", "EXACT_DUPLICATE", "PROBABLE_DUPLICATE"]
Strategy = Literal["append_new", "replace_range", "replace_selected"]


class ImportRowRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Id de la fila.")
    posted_at: date = Field(description="Fecha de la fila.")
    amount: Decimal = Field(description="Importe con signo (negativo = gasto).")
    raw_description: str = Field(description="Concepto tal como viene en el extracto.")
    classification: Classification = Field(
        description="`NEW`, `EXACT_DUPLICATE` o `PROBABLE_DUPLICATE` respecto a los "
        "movimientos de la cuenta."
    )
    matched_transaction_id: int | None = Field(
        description="Movimiento existente con el que coincide, si es un duplicado."
    )


class ImportPreview(BaseModel):
    id: int = Field(description="Id de la importación.")
    account_id: int = Field(description="Cuenta del extracto.")
    filename: str = Field(description="Nombre del archivo subido.")
    status: str = Field(description="`previewed` (pendiente) o `committed` (confirmada).")
    range_start: date = Field(description="Primera fecha del archivo.")
    range_end: date = Field(description="Última fecha del archivo.")
    created_at: datetime = Field(description="Fecha de subida.")
    new_count: int = Field(description="Filas nuevas.")
    exact_duplicate_count: int = Field(description="Filas que ya existen exactamente.")
    probable_duplicate_count: int = Field(description="Filas que probablemente ya existen.")
    rows: list[ImportRowRead] = Field(description="Filas del archivo, por fecha.")


class ImportCommitRequest(BaseModel):
    strategy: Strategy = Field(
        default="append_new",
        description="`append_new`, `replace_range` o `replace_selected` (ver la descripción "
        "del endpoint).",
        examples=["append_new"],
    )
    row_ids: list[int] = Field(
        default=[],
        description="Filas duplicadas que se quieren importar igualmente (o reemplazar, con "
        "`replace_selected`).",
        examples=[[1201, 1203]],
    )


class ImportCommitResult(BaseModel):
    id: int = Field(description="Id de la importación.")
    status: str = Field(description="Siempre `committed`.")
    strategy: Strategy = Field(description="Estrategia aplicada.")
    inserted_count: int = Field(description="Movimientos creados.")
    replaced_count: int = Field(description="Movimientos que se mandaron a la papelera.")
    skipped_count: int = Field(description="Filas que no se importaron.")
