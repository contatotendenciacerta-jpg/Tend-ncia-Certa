import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin
from app.models.subscription import Subscription
from app.models.subscription_tier import SubscriptionTier
from app.models.user import User
from app.schemas.admin_grants import GrantSubscriptionRequest, GrantSubscriptionResponse
from app.services.billing.subscription_service import grant_subscription

router = APIRouter(prefix="/admin/users", tags=["admin:grants"])


@router.post(
    "/{user_id}/grant-subscription",
    response_model=GrantSubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
def grant_subscription_route(
    user_id: uuid.UUID,
    payload: GrantSubscriptionRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> Subscription:
    """Test-only shortcut to activate a subscription without going through
    Stripe/Mercado Pago. Not meant to be exposed as a real product
    feature - admin-gated, and every grant is recorded with
    payment_provider=manual so it's easy to tell apart from real
    payments."""
    target_user = db.get(User, user_id)
    if target_user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuário não encontrado")

    tier = db.get(SubscriptionTier, payload.tier_id)
    if tier is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tier não encontrado")

    return grant_subscription(db, user_id=user_id, tier=tier, duration_days=payload.duration_days)
