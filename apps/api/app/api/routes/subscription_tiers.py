import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin
from app.models.subscription_tier import SubscriptionTier
from app.models.user import User
from app.schemas.subscription_tier import (
    SubscriptionTierCreate,
    SubscriptionTierRead,
    SubscriptionTierUpdate,
)

router = APIRouter(prefix="/admin/subscription-tiers", tags=["admin:subscription-tiers"])


@router.post("", response_model=SubscriptionTierRead, status_code=status.HTTP_201_CREATED)
def create_tier(
    payload: SubscriptionTierCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)
) -> SubscriptionTier:
    data = payload.model_dump()
    data["markets_allowed"] = [m.value for m in payload.markets_allowed]
    tier = SubscriptionTier(**data)
    db.add(tier)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Tier já cadastrado") from exc
    db.refresh(tier)
    return tier


@router.get("", response_model=list[SubscriptionTierRead])
def list_tiers(db: Session = Depends(get_db), _: User = Depends(require_admin)) -> list[SubscriptionTier]:
    return db.query(SubscriptionTier).order_by(SubscriptionTier.price_cents).all()


@router.get("/{tier_id}", response_model=SubscriptionTierRead)
def get_tier(
    tier_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_admin)
) -> SubscriptionTier:
    tier = db.get(SubscriptionTier, tier_id)
    if tier is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tier não encontrado")
    return tier


@router.put("/{tier_id}", response_model=SubscriptionTierRead)
def update_tier(
    tier_id: uuid.UUID,
    payload: SubscriptionTierUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> SubscriptionTier:
    tier = db.get(SubscriptionTier, tier_id)
    if tier is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tier não encontrado")

    update_data = payload.model_dump(exclude_unset=True)
    if "markets_allowed" in update_data and update_data["markets_allowed"] is not None:
        update_data["markets_allowed"] = [m.value for m in payload.markets_allowed]
    for field, value in update_data.items():
        setattr(tier, field, value)
    db.commit()
    db.refresh(tier)
    return tier


@router.delete("/{tier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tier(
    tier_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_admin)
) -> None:
    tier = db.get(SubscriptionTier, tier_id)
    if tier is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tier não encontrado")
    db.delete(tier)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Tier possui assinaturas vinculadas") from exc
