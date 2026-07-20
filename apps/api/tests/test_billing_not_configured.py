from app.core.config import settings
from app.core.security import hash_password
from app.models.subscription_tier import BillingInterval, SubscriptionTier, TierCode
from app.models.user import User, UserRole, UserStatus


def _create_subscriber(db) -> User:
    user = User(
        email="billingtest@example.com",
        password_hash=hash_password("supersecret"),
        name="Billing Test",
        role=UserRole.SUBSCRIBER,
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    db.commit()
    return user


def _create_tier(db) -> SubscriptionTier:
    tier = SubscriptionTier(
        code=TierCode.BASIC,
        name_i18n_key="tiers.basic.name",
        price_cents=1000,
        billing_interval=BillingInterval.MONTHLY,
        markets_allowed=["crypto"],
    )
    db.add(tier)
    db.commit()
    return tier


def _login(client, email: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": "supersecret"})
    return response.json()["access_token"]


def test_stripe_checkout_returns_503_when_api_key_missing(client, db, monkeypatch):
    monkeypatch.setattr(settings, "STRIPE_API_KEY", None)

    user = _create_subscriber(db)
    tier = _create_tier(db)
    token = _login(client, user.email)

    response = client.post(
        "/billing/stripe/checkout-session",
        json={"tier_id": str(tier.id)},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 503


def test_stripe_checkout_returns_503_when_webhook_secret_missing(client, db, monkeypatch):
    monkeypatch.setattr(settings, "STRIPE_WEBHOOK_SECRET", None)

    user = _create_subscriber(db)
    tier = _create_tier(db)
    token = _login(client, user.email)

    response = client.post(
        "/billing/stripe/checkout-session",
        json={"tier_id": str(tier.id)},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 503


def test_stripe_webhook_returns_503_when_not_configured(client, monkeypatch):
    monkeypatch.setattr(settings, "STRIPE_API_KEY", None)
    monkeypatch.setattr(settings, "STRIPE_WEBHOOK_SECRET", None)

    response = client.post(
        "/billing/stripe/webhook",
        content=b"{}",
        headers={"stripe-signature": "t=1,v1=whatever", "content-type": "application/json"},
    )

    assert response.status_code == 503


def test_mercadopago_preference_returns_503_when_not_configured(client, db, monkeypatch):
    monkeypatch.setattr(settings, "MERCADOPAGO_ACCESS_TOKEN", None)
    monkeypatch.setattr(settings, "MERCADOPAGO_WEBHOOK_SECRET", None)

    user = _create_subscriber(db)
    tier = _create_tier(db)
    token = _login(client, user.email)

    response = client.post(
        "/billing/mercadopago/preference",
        json={"tier_id": str(tier.id)},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 503


def test_mercadopago_webhook_returns_503_when_not_configured(client, monkeypatch):
    monkeypatch.setattr(settings, "MERCADOPAGO_ACCESS_TOKEN", None)
    monkeypatch.setattr(settings, "MERCADOPAGO_WEBHOOK_SECRET", None)

    response = client.post("/billing/mercadopago/webhook?type=payment&data.id=123")

    assert response.status_code == 503
