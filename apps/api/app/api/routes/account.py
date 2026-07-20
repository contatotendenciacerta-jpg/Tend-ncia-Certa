from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.account import MySubscriptionRead
from app.services.billing.subscription_service import get_active_subscription

router = APIRouter(prefix="/me", tags=["account"])


@router.get("/subscription", response_model=MySubscriptionRead)
def get_my_subscription(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> MySubscriptionRead:
    subscription = get_active_subscription(db, current_user.id)
    if subscription is None:
        return MySubscriptionRead(has_active_subscription=False)

    return MySubscriptionRead(
        has_active_subscription=True,
        tier=subscription.tier,
        status=subscription.status,
        current_period_end=subscription.current_period_end,
        pending_tier=subscription.pending_tier,
    )
