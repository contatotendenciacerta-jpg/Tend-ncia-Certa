from datetime import datetime

from pydantic import BaseModel

from app.models.subscription import SubscriptionStatus
from app.schemas.subscription_tier import SubscriptionTierRead


class MySubscriptionRead(BaseModel):
    has_active_subscription: bool
    tier: SubscriptionTierRead | None = None
    status: SubscriptionStatus | None = None
    current_period_end: datetime | None = None
    pending_tier: SubscriptionTierRead | None = None
