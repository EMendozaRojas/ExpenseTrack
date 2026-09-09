from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FxRate(Base):
    """Tasa de cambio fechada, cargada manualmente en esta primera versión
    (sin fetch automático diario del BCE). `rate` = cuánto vale 1 `base` en
    `quote` ese día."""

    __tablename__ = "fx_rates"
    __table_args__ = (UniqueConstraint("rate_date", "base", "quote", name="ux_fx_rates_date_pair"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    rate_date: Mapped[date] = mapped_column(Date, nullable=False)
    base: Mapped[str] = mapped_column(String(3), nullable=False)
    quote: Mapped[str] = mapped_column(String(3), nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
