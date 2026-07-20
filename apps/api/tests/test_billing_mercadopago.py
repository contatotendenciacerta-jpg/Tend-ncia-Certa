import hashlib
import hmac
import json
import uuid
from datetime import datetime, timedelta, timezone

from app.core.security import hash_password
from app.models.payment import Payment, PaymentStatus
from app.models.subscription import PaymentProvider, Subscription, SubscriptionStatus
from app.models.subscription_tier import BillingInterval, SubscriptionTier, TierCode
from app.models.user import User, UserRole, UserStatus
from app.services.billing import mercadopago_client

MP_WEBHOOK_SECRET = "mp-webhook-test-secret"


def _mp_signature_headers(*, data_id: str, request_id: str, secret: str = MP_WEBHOOK_SECRET, ts: str = "1704908010"):
    manifest = f"id:{data_id.lower()};request-id:{request_id};ts:{ts};"
    digest = hmac.new(secret.encode("utf-8"), manifest.encode("utf-8"), hashlib.sha256).hexdigest()
    return {"x-signature": f"ts={ts},v1={digest}", "x-request-id": request_id}


def _post_mp_notification(client, *, data_id: str, request_id: str = "req-1", secret: str = MP_WEBHOOK_SECRET):
    headers = _mp_signature_headers(data_id=data_id, request_id=request_id, secret=secret)
    return client.post(f"/billing/mercadopago/webhook?type=payment&data.id={data_id}", headers=headers)


# Example Payment resource shape per Mercado Pago's /v1/payments/{id} docs,
# trimmed to the fields our webhook handler actually reads.
def _make_mp_payment(*, payment_id, status, external_reference, transaction_amount=50.0, currency_id="BRL"):
    return {
        "id": payment_id,
        "status": status,
        "status_detail": "accredited" if status == "approved" else status,
        "transaction_amount": transaction_amount,
        "currency_id": currency_id,
        "external_reference": external_reference,
        "payment_method_id": "pix",
        "date_approved": "2026-07-20T12:00:00.000-04:00",
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


def _create_active_subscription(db, user, tier) -> Subscription:
    subscription = Subscription(
        user_id=user.id,
        tier_id=tier.id,
        status=SubscriptionStatus.ACTIVE,
        payment_provider=PaymentProvider.MERCADOPAGO,
        external_subscription_id=None,
        current_period_start=datetime.now(timezone.utc) - timedelta(days=1),
        current_period_end=datetime.now(timezone.utc) + timedelta(days=29),
    )
    db.add(subscription)
    db.commit()
    return subscription


def test_webhook_rejects_invalid_signature(client, db, monkeypatch):
    fetch_calls = []
    monkeypatch.setattr(mercadopago_client, "fetch_payment", lambda pid: fetch_calls.append(pid))

    response = client.post(
        "/billing/mercadopago/webhook?type=payment&data.id=123",
        headers={"x-signature": "ts=1,v1=deadbeef", "x-request-id": "req-1"},
    )

    assert response.status_code == 400
    assert fetch_calls == []  # must verify signature before ever calling the MP API


def test_approved_payment_activates_new_subscription(client, db, monkeypatch):
    user = _create_subscriber(db)
    tier = _create_tier(db, TierCode.BASIC, 1000)
    external_reference = json.dumps({"user_id": str(user.id), "tier_id": str(tier.id), "subscription_id": None})
    payment = _make_mp_payment(payment_id="mp_pay_1", status="approved", external_reference=external_reference, transaction_amount=10.0)

    monkeypatch.setattr(mercadopago_client, "fetch_payment", lambda pid: payment)

    response = _post_mp_notification(client, data_id="mp_pay_1")

    assert response.status_code == 200
    subscription = db.query(Subscription).filter(Subscription.user_id == user.id).one()
    assert subscription.status == SubscriptionStatus.ACTIVE
    assert subscription.tier_id == tier.id
    assert subscription.payment_provider == PaymentProvider.MERCADOPAGO

    payment_row = db.query(Payment).filter(Payment.subscription_id == subscription.id).one()
    assert payment_row.status == PaymentStatus.PAID
    assert payment_row.amount_cents == 1000
    assert payment_row.provider_reference == "mp_pay_1"


def test_approved_payment_renews_existing_subscription(client, db, monkeypatch):
    user = _create_subscriber(db)
    tier = _create_tier(db, TierCode.PRO, 5000)
    subscription = _create_active_subscription(db, user, tier)
    old_period_end = subscription.current_period_end

    external_reference = json.dumps(
        {"user_id": str(user.id), "tier_id": str(tier.id), "subscription_id": str(subscription.id)}
    )
    payment = _make_mp_payment(
        payment_id="mp_pay_2", status="approved", external_reference=external_reference, transaction_amount=50.0
    )
    monkeypatch.setattr(mercadopago_client, "fetch_payment", lambda pid: payment)

    response = _post_mp_notification(client, data_id="mp_pay_2")

    assert response.status_code == 200
    db.refresh(subscription)
    assert subscription.status == SubscriptionStatus.ACTIVE
    assert subscription.current_period_end > old_period_end
    assert db.query(Payment).filter(Payment.subscription_id == subscription.id).count() == 1


def test_rejected_payment_marks_existing_subscription_past_due(client, db, monkeypatch):
    user = _create_subscriber(db)
    tier = _create_tier(db, TierCode.PRO, 5000)
    subscription = _create_active_subscription(db, user, tier)

    external_reference = json.dumps(
        {"user_id": str(user.id), "tier_id": str(tier.id), "subscription_id": str(subscription.id)}
    )
    payment = _make_mp_payment(
        payment_id="mp_pay_3", status="rejected", external_reference=external_reference, transaction_amount=50.0
    )
    monkeypatch.setattr(mercadopago_client, "fetch_payment", lambda pid: payment)

    response = _post_mp_notification(client, data_id="mp_pay_3")

    assert response.status_code == 200
    db.refresh(subscription)
    assert subscription.status == SubscriptionStatus.PAST_DUE

    payment_row = db.query(Payment).filter(Payment.subscription_id == subscription.id).one()
    assert payment_row.status == PaymentStatus.FAILED


def test_rejected_payment_without_existing_subscription_is_a_noop(client, db, monkeypatch):
    user = _create_subscriber(db)
    tier = _create_tier(db, TierCode.BASIC, 1000)
    external_reference = json.dumps({"user_id": str(user.id), "tier_id": str(tier.id), "subscription_id": None})
    payment = _make_mp_payment(
        payment_id="mp_pay_4", status="rejected", external_reference=external_reference, transaction_amount=10.0
    )
    monkeypatch.setattr(mercadopago_client, "fetch_payment", lambda pid: payment)

    response = _post_mp_notification(client, data_id="mp_pay_4")

    assert response.status_code == 200
    assert db.query(Subscription).count() == 0
    assert db.query(Payment).count() == 0


def test_pending_payment_does_not_change_subscription_state(client, db, monkeypatch):
    user = _create_subscriber(db)
    tier = _create_tier(db, TierCode.PRO, 5000)
    subscription = _create_active_subscription(db, user, tier)

    external_reference = json.dumps(
        {"user_id": str(user.id), "tier_id": str(tier.id), "subscription_id": str(subscription.id)}
    )
    payment = _make_mp_payment(
        payment_id="mp_pay_5", status="pending", external_reference=external_reference, transaction_amount=50.0
    )
    monkeypatch.setattr(mercadopago_client, "fetch_payment", lambda pid: payment)

    response = _post_mp_notification(client, data_id="mp_pay_5")

    assert response.status_code == 200
    db.refresh(subscription)
    assert subscription.status == SubscriptionStatus.ACTIVE
    assert db.query(Payment).count() == 0


def test_cancelled_payment_marks_subscription_canceled(client, db, monkeypatch):
    user = _create_subscriber(db)
    tier = _create_tier(db, TierCode.PRO, 5000)
    subscription = _create_active_subscription(db, user, tier)

    external_reference = json.dumps(
        {"user_id": str(user.id), "tier_id": str(tier.id), "subscription_id": str(subscription.id)}
    )
    payment = _make_mp_payment(
        payment_id="mp_pay_6", status="cancelled", external_reference=external_reference, transaction_amount=50.0
    )
    monkeypatch.setattr(mercadopago_client, "fetch_payment", lambda pid: payment)

    response = _post_mp_notification(client, data_id="mp_pay_6")

    assert response.status_code == 200
    db.refresh(subscription)
    assert subscription.status == SubscriptionStatus.CANCELED


def test_non_payment_notification_types_are_ignored(client, db, monkeypatch):
    fetch_calls = []
    monkeypatch.setattr(mercadopago_client, "fetch_payment", lambda pid: fetch_calls.append(pid))

    response = client.post("/billing/mercadopago/webhook?type=merchant_order&data.id=999")

    assert response.status_code == 200
    assert fetch_calls == []
