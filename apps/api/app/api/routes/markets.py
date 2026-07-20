import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin
from app.models.market import Market
from app.models.user import User
from app.schemas.market import MarketCreate, MarketRead, MarketUpdate

router = APIRouter(prefix="/admin/markets", tags=["admin:markets"])


@router.post("", response_model=MarketRead, status_code=status.HTTP_201_CREATED)
def create_market(
    payload: MarketCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)
) -> Market:
    market = Market(**payload.model_dump())
    db.add(market)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Mercado já cadastrado") from exc
    db.refresh(market)
    return market


@router.get("", response_model=list[MarketRead])
def list_markets(db: Session = Depends(get_db), _: User = Depends(require_admin)) -> list[Market]:
    return db.query(Market).order_by(Market.name_i18n_key).all()


@router.get("/{market_id}", response_model=MarketRead)
def get_market(
    market_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_admin)
) -> Market:
    market = db.get(Market, market_id)
    if market is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Mercado não encontrado")
    return market


@router.put("/{market_id}", response_model=MarketRead)
def update_market(
    market_id: uuid.UUID,
    payload: MarketUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> Market:
    market = db.get(Market, market_id)
    if market is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Mercado não encontrado")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(market, field, value)
    db.commit()
    db.refresh(market)
    return market


@router.delete("/{market_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_market(
    market_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_admin)
) -> None:
    market = db.get(Market, market_id)
    if market is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Mercado não encontrado")
    db.delete(market)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Mercado possui ativos vinculados") from exc
