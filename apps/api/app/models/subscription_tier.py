import enum

from sqlalchemy import ARRAY, Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, pg_enum


class TierCode(str, enum.Enum):
    BASIC = "basic"
    PRO = "pro"
    VIP = "vip"


class BillingInterval(str, enum.Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"


class SubscriptionTier(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "subscription_tiers"

    code: Mapped[TierCode] = mapped_column(pg_enum(TierCode, "tier_code"), unique=True, nullable=False)
    name_i18n_key: Mapped[str] = mapped_column(String(255), nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="BRL")
    billing_interval: Mapped[BillingInterval] = mapped_column(
        pg_enum(BillingInterval, "billing_interval"), nullable=False
    )
    markets_allowed: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    signal_delay_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_active_signals_visible: Mapped[int | None] = mapped_column(Integer, nullable=True)
    allows_vip_only_signals: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    push_notifications: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
