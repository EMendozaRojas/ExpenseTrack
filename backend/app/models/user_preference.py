from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

DEFAULT_BASE_CURRENCY = "EUR"
DEFAULT_LOCALE = "es-ES"
DEFAULT_ANT_MAX_AMOUNT = Decimal("10.00")
DEFAULT_ANT_MIN_OCCURRENCES = 5
DEFAULT_ANT_MIN_AGGREGATE = Decimal("30.00")


class UserPreferences(Base):
    """Preferencias del usuario: regionales (moneda, locale) y de insights
    (umbrales de 'gasto hormiga'). Una fila por usuario, creada con valores
    por defecto en el primer acceso a cualquiera de las dos."""

    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False, default=DEFAULT_BASE_CURRENCY)
    locale: Mapped[str] = mapped_column(String(10), nullable=False, default=DEFAULT_LOCALE)
    ant_max_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=DEFAULT_ANT_MAX_AMOUNT
    )
    ant_min_occurrences: Mapped[int] = mapped_column(
        Integer, nullable=False, default=DEFAULT_ANT_MIN_OCCURRENCES
    )
    ant_min_aggregate: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=DEFAULT_ANT_MIN_AGGREGATE
    )
