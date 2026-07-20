import hashlib
import hmac
import json
import time
import uuid
from datetime import datetime, timedelta, timezone

from app.core.security import hash_password
from app.models.payment import Payment, PaymentStatus
from app.models.subscription import PaymentProvider, Subscription, SubscriptionStatus
from app.models.subscription_tier import BillingInterval, SubscriptionTier, TierCode
from app.models.user import User, UserRole, UserStatus
from app.services.billing import stripe_client

STRIPE_WEBHOOK_SECRET = "whsec_test_dummy"


def _stripe_signature_header(payload: bytes, secret: str = STRIPE_WEBHOOK_SECRET) -> str:
    timestamp = int(time.time())
    signed_payload = f"{timestamp}.{payload.decode('utf-8')}".encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={signature}"


def _post_stripe_event(client, event: dict, *, secret: str = STRIPE_WEBHOOK_SECRET):
    payload = json.dumps(event).encode("utf-8")
    return client.post(
        "/billing/stripe/webhook",
        content=payload,
        headers={"stripe-signature": _stripe_signature_header(payload, secret), "content-type": "application/json"},
    )


def _make_checkout_completed_event(*, user_id, tier_id, subscription_id, amount_total=5000, upgrade_from=""):
    return {
        "id": "evt_test_1",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_123",
                "subscription": subscription_id,
                "amount_total": amount_total,
                "currency": "brl",
                "metadata": {
                    "user_id": str(user_id),
                    "tier_id": str(tier_id),
                    "upgrade_from_subscription_id": upgrade_from,
                },
            }
        },
    }


def _make_invoice_payment_failed_event(*, subscription_id, amount_due=5000):
    return {
        "id": "evt_test_2",
        "type": "invoice.payment_failed",
        "data": {
            "object": {
                "id": "in_test_123",
                "subscription": subscription_id,
                "amount_due": amount_due,
                "currency": "brl",
            }
        },
    }


def _make_subscription_deleted_event(*, subscription_id):
    return {
        "id": "evt_test_3",
        "type": "customer.subscription.deleted",
        "data": {"object": {"id": subscription_id}},
    }


def _create_subscriber(db) -> User:
    user = User(
        email=f"{uuid.uuid4()}@example.com",
        password_hash=hash_password("supersecret"),
        name="Subscriber",
        role=UserRole.SUBSCRIBER,
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    db.commit()
    return user


def _create_tier(db, code: TierCode, price_cents: int) -> SubscriptionTier:
    tier = SubscriptionTier(
        code=code,
        name_i18n_key=f"tiers.{code.value}.name",
        price_cents=price_cents,
        billing_interval=BillingInterval.MONTHLY,
        markets_allowed=["crypto"],
    )
    db.add(tier)
    db.commit()
    return tier


def _create_active_subscription(db, user, tier, external_subscription_id) -> Subscription:
    subscription = Subscription(
        user_id=user.id,
        tier_id=tier.id,
        status=SubscriptionStatus.ACTIVE,
        payment_provider=PaymentProvider.STRIPE,
        external_subscription_id=external_subscription_id,
        current_period_start=datetime.now(timezone.utc) - timedelta(days=1),
        current_period_end=datetime.now(timezone.utc) + timedelta(days=29),
    )
    db.add(subscription)
    db.commit()
    return subscription


def test_webhook_rejects_invalid_signature(client, db):
    user = _create_subscriber(db)
    tier = _create_tier(db, TierCode.BASIC, 1000)
    event = _make_checkout_completed_event(user_id=user.id, tier_id=tier.id, subscription_id="sub_bad")
    payload = json.dumps(event).encode("utf-8")

    response = client.post(
        "/billing/stripe/webhook",
        content=payload,
        headers={"stripe-signature": "t=1,v1=deadbeef", "content-type": "application/json"},
    )

    assert response.status_code == 400
    assert db.query(Subscription).count() == 0


def test_checkout_completed_activates_new_subscription(client, db):
    user = _create_subscriber(db)
    tier = _create_tier(db, TierCode.BASIC, 1000)
    event = _make_checkout_completed_event(
        user_id=user.id, tier_id=tier.id, subscription_id="sub_new_123", amount_total=1000
    )

    response = _post_stripe_event(client, event)

    assert response.status_code == 200
    subscription = db.query(Subscription).filter(Subscription.user_id == user.id).one()
    assert subscription.status == SubscriptionStatus.ACTIVE
    assert subscription.tier_id == tier.id
    assert subscription.external_subscription_id == "sub_new_123"

    payment = db.query(Payment).filter(Payment.subscription_id == subscription.id).one()
    assert payment.status == PaymentStatus.PAID
    assert payment.amount_cents == 1000
    assert payment.provider_reference == "cs_test_123"


def test_checkout_completed_upgrade_cancels_old_and_activates_new(client, db, monkeypatch):
    canceled_ids = []
    monkeypatch.setattr(stripe_client, "cancel_subscription", lambda sub_id: canceled_ids.append(sub_id))

    user = _create_subscriber(db)
    basic_tier = _create_tier(db, TierCode.BASIC, 1000)
    vip_tier = _create_tier(db, TierCode.VIP, 9000)
    old_subscription = _create_active_subscription(db, user, basic_tier, "sub_old_123")

    event = _make_checkout_completed_event(
        user_id=user.id,
        tier_id=vip_tier.id,
        subscription_id="sub_new_456",
        amount_total=9000,
        upgrade_from=str(old_subscription.id),
    )

    response = _post_stripe_event(client, event)

    assert response.status_code == 200
    assert canceled_ids == ["sub_old_123"]

    db.refresh(old_subscription)
    assert old_subscription.status == SubscriptionStatus.CANCELED

    new_subscription = (
        db.query(Subscription).filter(Subscription.external_subscription_id == "sub_new_456").one()
    )
    assert new_subscription.status == SubscriptionStatus.ACTIVE
    assert new_subscription.tier_id == vip_tier.id


def test_invoice_payment_failed_marks_past_due(client, db):
    user = _create_subscriber(db)
    tier = _create_tier(db, TierCode.PRO, 5000)
    subscription = _create_active_subscription(db, user, tier, "sub_pd_123")

    event = _make_invoice_payment_failed_event(subscription_id="sub_pd_123", amount_due=5000)
    response = _post_stripe_event(client, event)

    assert response.status_code == 200
    db.refresh(subscription)
    assert subscription.status == SubscriptionStatus.PAST_DUE

    payment = db.query(Payment).filter(Payment.subscription_id == subscription.id).one()
    assert payment.status == PaymentStatus.FAILED
    assert payment.amount_cents == 5000


def test_subscription_deleted_marks_canceled(client, db):
    user = _create_subscriber(db)
    tier = _create_tier(db, TierCode.PRO, 5000)
    subscription = _create_active_subscription(db, user, tier, "sub_del_123")

    event = _make_subscription_deleted_event(subscription_id="sub_del_123")
    response = _post_stripe_event(client, event)

    assert response.status_code == 200
    db.refresh(subscription)
    assert subscription.status == SubscriptionStatus.CANCELED


def test_unknown_external_subscription_id_is_ignored(client, db):
    event = _make_invoice_payment_failed_event(subscription_id="sub_does_not_exist")
    response = _post_stripe_event(client, event)

    assert response.status_code == 200
    assert db.query(Subscription).count() == 0
