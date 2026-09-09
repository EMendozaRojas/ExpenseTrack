from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.fx_rate import FxRate
from app.models.user import User
from app.schemas.fx_rate import FxRateCreate, FxRateRead

router = APIRouter(prefix="/fx-rates", tags=["fx-rates"])


@router.get("/", response_model=list[FxRateRead])
def list_fx_rates(
    db: Annotated[Session, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_current_user)],
    base: str | None = None,
    quote: str | None = None,
) -> list[FxRateRead]:
    query = db.query(FxRate)
    if base is not None:
        query = query.filter(FxRate.base == base.upper())
    if quote is not None:
        query = query.filter(FxRate.quote == quote.upper())
    return query.order_by(FxRate.rate_date.desc()).all()


@router.post("/", response_model=FxRateRead, status_code=status.HTTP_201_CREATED)
def create_fx_rate(
    payload: FxRateCreate,
    db: Annotated[Session, Depends(get_db)],
    _current_user: Annotated[User, Depends(get_current_user)],
) -> FxRateRead:
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
    return fx_rate
