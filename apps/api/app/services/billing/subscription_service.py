import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum

from sqlalchemy.orm import Session

from app.models.payment import Payment, PaymentStatus
from app.models.subscription import PaymentProvider, Subscription, SubscriptionStatus
from app.models.subscription_tier import BillingInterval, SubscriptionTier

ACTIVE_SUBSCRIPTION_STATUSES = (SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING)

# Stripe drives its own billing cycle natively; Mercado Pago (Checkout Pro)
# does not, so we track the period ourselves using the tier's interval.
BILLING_INTERVAL_TIMEDELTA = {
    BillingInterval.MONTHLY: timedelta(days=30),
    BillingInterval.YEARLY: timedelta(days=365),
}


class TierChangeDecision(str, Enum):
    NEW = "new"
    SAME = "same"
    UPGRADE = "upgrade"
    DOWNGRADE = "downgrade"


def get_active_subscription(db: Session, user_id: uuid.UUID) -> Subscription | None:
    return (
        db.query(Subscription)
        .filter(Subscription.user_id == user_id, Subscription.status.in_(ACTIVE_SUBSCRIPTION_STATUSES))
        .order_by(Subscription.created_at.desc())
        .first()
    )


def find_by_external_subscription_id(db: Session, external_subscription_id: str) -> Subscription | None:
    return (
        db.query(Subscription)
        .filter(Subscription.external_subscription_id == external_subscription_id)
        .first()
    )


def resolve_tier_change(
    active_subscription: Subscription | None, new_tier: SubscriptionTier
) -> TierChangeDecision:
    if active_subscription is None:
        return TierChangeDecision.NEW
    if active_subscription.tier_id == new_tier.id:
        return TierChangeDecision.SAME
    if new_tier.price_cents > active_subscription.tier.price_cents:
        return TierChangeDecision.UPGRADE
    return TierChangeDecision.DOWNGRADE


def schedule_downgrade(db: Session, subscription: Subscription, new_tier: SubscriptionTier) -> Subscription:
    subscription.pending_tier_id = new_tier.id
    db.commit()
    db.refresh(subscription)
    return subscription


def apply_due_downgrades(db: Session, now: datetime | None = None) -> int:
    """Applies scheduled downgrades whose current period has already ended.

    Not wired to a scheduler yet (no cron/Celery beat in this codebase) -
    call periodically from an operational job once one exists.
    """
    now = now or datetime.now(timezone.utc)
    due = (
        db.query(Subscription)
        .filter(Subscription.pending_tier_id.isnot(None), Subscription.current_period_end <= now)
        .all()
    )
    for subscription in due:
        subscription.tier_id = subscription.pending_tier_id
        subscription.pending_tier_id = None
    db.commit()
    return len(due)


def activate_new_subscription(
    db: Session,
    *,
    user_id: uuid.UUID,
    tier: SubscriptionTier,
    payment_provider: PaymentProvider,
    external_subscription_id: str | None,
    amount_cents: int,
    currency: str,
    provider_reference: str,
    cancel_subscription_row_id: uuid.UUID | None = None,
) -> Subscription:
    now = datetime.now(timezone.utc)

    if cancel_subscription_row_id is not None:
        old = db.get(Subscription, cancel_subscription_row_id)
        if old is not None:
            old.status = SubscriptionStatus.CANCELED

    subscription = Subscription(
        user_id=user_id,
        tier_id=tier.id,
        status=SubscriptionStatus.ACTIVE,
        payment_provider=payment_provider,
        external_subscription_id=external_subscription_id,
        current_period_start=now,
        current_period_end=now + BILLING_INTERVAL_TIMEDELTA[tier.billing_interval],
        cancel_at_period_end=False,
    )
    db.add(subscription)
    db.flush()

    db.add(
        Payment(
            subscription_id=subscription.id,
            amount_cents=amount_cents,
            currency=currency,
            status=PaymentStatus.PAID,
            provider_reference=provider_reference,
            paid_at=now,
        )
    )
    db.commit()
    db.refresh(subscription)
    return subscription


def renew_or_upgrade_subscription(
    db: Session,
    *,
    subscription: Subscription,
    tier: SubscriptionTier,
    amount_cents: int,
    currency: str,
    provider_reference: str,
) -> Subscription:
    now = datetime.now(timezone.utc)

    subscription.tier_id = tier.id
    subscription.status = SubscriptionStatus.ACTIVE
    subscription.current_period_start = now
    subscription.current_period_end = now + BILLING_INTERVAL_TIMEDELTA[tier.billing_interval]
    if subscription.pending_tier_id == tier.id:
        subscription.pending_tier_id = None

    db.add(
        Payment(
            subscription_id=subscription.id,
            amount_cents=amount_cents,
            currency=currency,
            status=PaymentStatus.PAID,
            provider_reference=provider_reference,
            paid_at=now,
        )
    )
    db.commit()
    db.refresh(subscription)
    return subscription


def mark_past_due(
    db: Session,
    subscription: Subscription,
    *,
    amount_cents: int | None,
    currency: str,
    provider_reference: str,
) -> Subscription:
    subscription.status = SubscriptionStatus.PAST_DUE
    if amount_cents is not None:
        db.add(
            Payment(
                subscription_id=subscription.id,
                amount_cents=amount_cents,
                currency=currency,
                status=PaymentStatus.FAILED,
                provider_reference=provider_reference,
                paid_at=None,
            )
        )
    db.commit()
    db.refresh(subscription)
    return subscription


def mark_canceled(db: Session, subscription: Subscription) -> Subscription:
    subscription.status = SubscriptionStatus.CANCELED
    db.commit()
    db.refresh(subscription)
    return subscription


def grant_subscription(
    db: Session, *, user_id: uuid.UUID, tier: SubscriptionTier, duration_days: int
) -> Subscription:
    """Admin-only test helper: activates a subscription with no Payment
    record and no payment provider involved. See
    POST /admin/users/{id}/grant-subscription."""
    now = datetime.now(timezone.utc)

    existing = get_active_subscription(db, user_id)
    if existing is not None:
        existing.status = SubscriptionStatus.CANCELED

    subscription = Subscription(
        user_id=user_id,
        tier_id=tier.id,
        status=SubscriptionStatus.ACTIVE,
        payment_provider=PaymentProvider.MANUAL,
        external_subscription_id=None,
        current_period_start=now,
        current_period_end=now + timedelta(days=duration_days),
        cancel_at_period_end=False,
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription
