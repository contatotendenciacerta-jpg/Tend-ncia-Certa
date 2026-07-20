import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.market import MarketCode
from app.models.subscription_tier import BillingInterval, TierCode


class SubscriptionTierCreate(BaseModel):
    code: TierCode
    name_i18n_key: str = Field(min_length=1, max_length=255)
    price_cents: int = Field(ge=0)
    currency: str = Field(default="BRL", min_length=3, max_length=3)
    billing_interval: BillingInterval
    markets_allowed: list[MarketCode] = Field(default_factory=list)
    signal_delay_minutes: int = Field(default=0, ge=0)
    max_active_signals_visible: int | None = Field(default=None, ge=0)
    allows_vip_only_signals: bool = False
    push_notifications: bool = False
    is_active: bool = True


class SubscriptionTierUpdate(BaseModel):
    name_i18n_key: str | None = Field(default=None, min_length=1, max_length=255)
    price_cents: int | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    billing_interval: BillingInterval | None = None
    markets_allowed: list[MarketCode] | None = None
    signal_delay_minutes: int | None = Field(default=None, ge=0)
    max_active_signals_visible: int | None = Field(default=None, ge=0)
    allows_vip_only_signals: bool | None = None
    push_notifications: bool | None = None
    is_active: bool | None = None


class SubscriptionTierRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: TierCode
    name_i18n_key: str
    price_cents: int
    currency: str
    billing_interval: BillingInterval
    markets_allowed: list[str]
    signal_delay_minutes: int
    max_active_signals_visible: int | None
    allows_vip_only_signals: bool
    push_notifications: bool
    is_active: bool
