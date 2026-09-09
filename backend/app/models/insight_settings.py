from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

DEFAULT_ANT_MAX_AMOUNT = Decimal("10.00")
DEFAULT_ANT_MIN_OCCURRENCES = 5
DEFAULT_ANT_MIN_AGGREGATE = Decimal("30.00")


class InsightSettings(Base):
    """Umbrales de 'gasto hormiga' configurables por el usuario. Una fila
    por usuario, creada con valores por defecto en el primer acceso."""

    __tablename__ = "insight_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    ant_max_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=DEFAULT_ANT_MAX_AMOUNT
    )
    ant_min_occurrences: Mapped[int] = mapped_column(
        Integer, nullable=False, default=DEFAULT_ANT_MIN_OCCURRENCES
    )
    ant_min_aggregate: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=DEFAULT_ANT_MIN_AGGREGATE
    )
