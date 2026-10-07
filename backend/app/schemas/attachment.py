from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AttachmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Id del adjunto.")
    transaction_id: int = Field(description="Movimiento al que pertenece.")
    filename: str = Field(description="Nombre original del archivo.")
    mime_type: str = Field(description="Tipo de contenido (`image/jpeg`, `application/pdf`…).")
    size_bytes: int = Field(description="Tamaño en bytes.")
    created_at: datetime = Field(description="Fecha de subida.")
