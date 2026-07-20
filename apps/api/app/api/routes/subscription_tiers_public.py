from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.subscription_tier import SubscriptionTier
from app.schemas.subscription_tier import SubscriptionTierRead

router = APIRouter(tags=["subscription-tiers"])


@router.get("/subscription-tiers", response_model=list[SubscriptionTierRead])
def list_public_tiers(db: Session = Depends(get_db)) -> list[SubscriptionTier]:
    return (
        db.query(SubscriptionTier)
        .filter(SubscriptionTier.is_active.is_(True))
        .order_by(SubscriptionTier.price_cents)
        .all()
    )
