"""Conversión entre divisas usando tasas cargadas manualmente en `fx_rates`.

Sin fetch automático diario del BCE en esta versión: el usuario (o un
proceso futuro) carga la tasa de un día concreto vía `POST /fx-rates` antes
de poder registrar un movimiento en una divisa distinta a la de la cuenta.
"""

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.fx_rate import FxRate


class MissingFxRateError(Exception):
    def __init__(self, rate_date: date, from_currency: str, to_currency: str) -> None:
        self.rate_date = rate_date
        self.from_currency = from_currency
        self.to_currency = to_currency
        super().__init__(
            f"Falta la tasa de cambio {from_currency}->{to_currency} para {rate_date.isoformat()}"
        )


def convert(
    db: Session, amount: Decimal, from_currency: str, to_currency: str, on_date: date
) -> tuple[Decimal, Decimal]:
    """Devuelve (importe_convertido, tasa_aplicada).

    Busca primero la tasa directa (base=from, quote=to); si no existe,
    prueba la inversa (base=to, quote=from).
    """
    if from_currency == to_currency:
        return amount, Decimal("1")

    direct = (
        db.query(FxRate)
        .filter(FxRate.rate_date == on_date, FxRate.base == from_currency, FxRate.quote == to_currency)
        .first()
    )
    if direct is not None:
        return (amount * direct.rate).quantize(Decimal("0.01")), direct.rate

    inverse = (
        db.query(FxRate)
        .filter(FxRate.rate_date == on_date, FxRate.base == to_currency, FxRate.quote == from_currency)
        .first()
    )
    if inverse is not None:
        rate = Decimal("1") / inverse.rate
        return (amount * rate).quantize(Decimal("0.01")), rate.quantize(Decimal("0.000001"))

    raise MissingFxRateError(on_date, from_currency, to_currency)
