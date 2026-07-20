import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.subscription import PaymentProvider, SubscriptionStatus


class GrantSubscriptionRequest(BaseModel):
    tier_id: uuid.UUID
    duration_days: int = Field(default=30, ge=1, le=3650)


class GrantSubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    tier_id: uuid.UUID
    status: SubscriptionStatus
    payment_provider: PaymentProvider
    current_period_start: datetime
    current_period_end: datetime
