import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.core.security import hash_password
from app.models.subscription import PaymentProvider, Subscription, SubscriptionStatus
from app.models.subscription_tier import BillingInterval, SubscriptionTier, TierCode
from app.models.user import User, UserRole, UserStatus
from app.services.billing import mercadopago_client, stripe_client
from app.services.billing.subscription_service import apply_due_downgrades


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


def _create_active_subscription(db, user, tier, provider=PaymentProvider.STRIPE) -> Subscription:
    subscription = Subscription(
        user_id=user.id,
        tier_id=tier.id,
        status=SubscriptionStatus.ACTIVE,
        payment_provider=provider,
        external_subscription_id="sub_existing" if provider == PaymentProvider.STRIPE else None,
        current_period_start=datetime.now(timezone.utc) - timedelta(days=1),
        current_period_end=datetime.now(timezone.utc) + timedelta(days=29),
    )
    db.add(subscription)
    db.commit()
    return subscription


def _login(client, email: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": "supersecret"})
    return response.json()["access_token"]


def test_stripe_checkout_session_created_for_new_subscriber(client, db, monkeypatch):
    captured = {}

    def _fake_create_checkout_session(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(url="https://checkout.stripe.com/fake-session")

    monkeypatch.setattr(stripe_client, "create_checkout_session", _fake_create_checkout_session)

    user = _create_subscriber(db)
    tier = _create_tier(db, TierCode.BASIC, 1000)
    token = _login(client, user.email)

    response = client.post(
        "/billing/stripe/checkout-session",
        json={"tier_id": str(tier.id)},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    assert response.json()["checkout_url"] == "https://checkout.stripe.com/fake-session"
    assert captured["metadata"]["upgrade_from_subscription_id"] == ""


def test_stripe_checkout_rejects_same_tier(client, db, monkeypatch):
    monkeypatch.setattr(
        stripe_client, "create_checkout_session", lambda **kw: SimpleNamespace(url="https://unused")
    )

    user = _create_subscriber(db)
    tier = _create_tier(db, TierCode.PRO, 5000)
    _create_active_subscription(db, user, tier)
    token = _login(client, user.email)

    response = client.post(
        "/billing/stripe/checkout-session",
        json={"tier_id": str(tier.id)},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409


def test_stripe_checkout_marks_upgrade_in_metadata(client, db, monkeypatch):
    captured = {}

    def _fake_create_checkout_session(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(url="https://checkout.stripe.com/fake-upgrade")

    monkeypatch.setattr(stripe_client, "create_checkout_session", _fake_create_checkout_session)

    user = _create_subscriber(db)
    basic_tier = _create_tier(db, TierCode.BASIC, 1000)
    vip_tier = _create_tier(db, TierCode.VIP, 9000)
    old_subscription = _create_active_subscription(db, user, basic_tier)
    token = _login(client, user.email)

    response = client.post(
        "/billing/stripe/checkout-session",
        json={"tier_id": str(vip_tier.id)},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    assert captured["metadata"]["upgrade_from_subscription_id"] == str(old_subscription.id)


def test_stripe_checkout_schedules_downgrade_without_creating_session(client, db, monkeypatch):
    calls = []
    monkeypatch.setattr(stripe_client, "create_checkout_session", lambda **kw: calls.append(kw))

    user = _create_subscriber(db)
    basic_tier = _create_tier(db, TierCode.BASIC, 1000)
    vip_tier = _create_tier(db, TierCode.VIP, 9000)
    subscription = _create_active_subscription(db, user, vip_tier)
    token = _login(client, user.email)

    response = client.post(
        "/billing/stripe/checkout-session",
        json={"tier_id": str(basic_tier.id)},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    assert response.json()["scheduled_downgrade"] is True
    assert calls == []  # never talks to Stripe for a downgrade

    db.refresh(subscription)
    assert subscription.pending_tier_id == basic_tier.id
    assert subscription.tier_id == vip_tier.id  # not applied yet


def test_mercadopago_preference_created_for_new_subscriber(client, db, monkeypatch):
    monkeypatch.setattr(
        mercadopago_client,
        "create_preference",
        lambda **kw: {"init_point": "https://mp.example/checkout", "id": "pref_123"},
    )

    user = _create_subscriber(db)
    tier = _create_tier(db, TierCode.BASIC, 1000)
    token = _login(client, user.email)

    response = client.post(
        "/billing/mercadopago/preference",
        json={"tier_id": str(tier.id)},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    assert response.json() == {"checkout_url": "https://mp.example/checkout", "preference_id": "pref_123"}


def test_mercadopago_preference_allows_same_tier_renewal(client, db, monkeypatch):
    monkeypatch.setattr(
        mercadopago_client,
        "create_preference",
        lambda **kw: {"init_point": "https://mp.example/renew", "id": "pref_456"},
    )

    user = _create_subscriber(db)
    tier = _create_tier(db, TierCode.PRO, 5000)
    _create_active_subscription(db, user, tier, provider=PaymentProvider.MERCADOPAGO)
    token = _login(client, user.email)

    response = client.post(
        "/billing/mercadopago/preference",
        json={"tier_id": str(tier.id)},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Unlike Stripe, MP has no native recurring billing here - renewing the
    # same tier must go through a new preference each period.
    assert response.status_code == 201


def test_mercadopago_preference_schedules_downgrade_without_creating_preference(client, db, monkeypatch):
    calls = []
    monkeypatch.setattr(mercadopago_client, "create_preference", lambda **kw: calls.append(kw))

    user = _create_subscriber(db)
    basic_tier = _create_tier(db, TierCode.BASIC, 1000)
    vip_tier = _create_tier(db, TierCode.VIP, 9000)
    subscription = _create_active_subscription(db, user, vip_tier, provider=PaymentProvider.MERCADOPAGO)
    token = _login(client, user.email)

    response = client.post(
        "/billing/mercadopago/preference",
        json={"tier_id": str(basic_tier.id)},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    assert response.json()["scheduled_downgrade"] is True
    assert calls == []

    db.refresh(subscription)
    assert subscription.pending_tier_id == basic_tier.id


def test_apply_due_downgrades_applies_only_expired_periods(db):
    user = _create_subscriber(db)
    vip_tier = _create_tier(db, TierCode.VIP, 9000)
    basic_tier = _create_tier(db, TierCode.BASIC, 1000)

    expired_subscription = Subscription(
        user_id=user.id,
        tier_id=vip_tier.id,
        pending_tier_id=basic_tier.id,
        status=SubscriptionStatus.ACTIVE,
        payment_provider=PaymentProvider.STRIPE,
        current_period_start=datetime.now(timezone.utc) - timedelta(days=31),
        current_period_end=datetime.now(timezone.utc) - timedelta(days=1),
    )
    still_active_subscription = Subscription(
        user_id=user.id,
        tier_id=vip_tier.id,
        pending_tier_id=basic_tier.id,
        status=SubscriptionStatus.ACTIVE,
        payment_provider=PaymentProvider.STRIPE,
        current_period_start=datetime.now(timezone.utc) - timedelta(days=1),
        current_period_end=datetime.now(timezone.utc) + timedelta(days=29),
    )
    db.add_all([expired_subscription, still_active_subscription])
    db.commit()

    applied_count = apply_due_downgrades(db)

    assert applied_count == 1
    db.refresh(expired_subscription)
    db.refresh(still_active_subscription)
    assert expired_subscription.tier_id == basic_tier.id
    assert expired_subscription.pending_tier_id is None
    assert still_active_subscription.tier_id == vip_tier.id
    assert still_active_subscription.pending_tier_id == basic_tier.id
