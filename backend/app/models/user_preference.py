from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

DEFAULT_BASE_CURRENCY = "EUR"
DEFAULT_LOCALE = "es-ES"


class UserPreferences(Base):
    """Preferencias regionales del usuario. Una fila por usuario, creada con
    valores por defecto en el primer acceso."""

    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False, default=DEFAULT_BASE_CURRENCY)
    locale: Mapped[str] = mapped_column(String(10), nullable=False, default=DEFAULT_LOCALE)
