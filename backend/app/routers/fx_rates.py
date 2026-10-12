from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.core.openapi import AUTH_RESPONSES, Tag, error_responses
from app.models.fx_rate import FxRate
from app.models.user import User
from app.schemas.fx_rate import FxRateCreate, FxRateRead

router = APIRouter(prefix="/fx-rates", tags=[Tag.TIPOS_DE_CAMBIO], responses=AUTH_RESPONSES)


@router.get("/", response_model=list[FxRateRead], summary="Listar tipos de cambio")
def list_fx_rates(
    db: Annotated[Session, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_current_user)],
    base: Annotated[
        str | None, Query(description="Solo con esta moneda de origen.", examples=["USD"])
    ] = None,
    quote: Annotated[
        str | None, Query(description="Solo con esta moneda de destino.", examples=["EUR"])
    ] = None,
) -> list[FxRateRead]:
    """Tipos de cambio cargados, del más reciente al más antiguo. Son
    comunes a todos los usuarios."""
    query = db.query(FxRate)
    if base is not None:
        query = query.filter(FxRate.base == base.upper())
    if quote is not None:
        query = query.filter(FxRate.quote == quote.upper())
    return [FxRateRead.model_validate(rate) for rate in query.order_by(FxRate.rate_date.desc())]


@router.post(
    "/",
    response_model=FxRateRead,
    status_code=status.HTTP_201_CREATED,
    summary="Cargar un tipo de cambio",
    responses=error_responses(
        409,
        e409=(
            "Ya hay un tipo de cambio para esa fecha y ese par de monedas.",
            "Ya existe una tasa para esa fecha y ese par de divisas",
        ),
    ),
)
def create_fx_rate(
    payload: FxRateCreate,
    db: Annotated[Session, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_current_user)],
) -> FxRateRead:
    """Carga el tipo de cambio de un día. Al registrar un movimiento en otra
    moneda se usa el de su fecha: el directo (`base` → `quote`) o, si no
    existe, el inverso. Sin tipo de cambio para ese día, el movimiento se
    rechaza con `422`."""
    existing = (
        db.query(FxRate)
        .filter(
            FxRate.rate_date == payload.rate_date,
            FxRate.base == payload.base,
            FxRate.quote == payload.quote,
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una tasa para esa fecha y ese par de divisas",
        )

    fx_rate = FxRate(
        rate_date=payload.rate_date, base=payload.base, quote=payload.quote, rate=payload.rate
    )
    db.add(fx_rate)
    db.commit()
    db.refresh(fx_rate)
    return FxRateRead.model_validate(fx_rate)
