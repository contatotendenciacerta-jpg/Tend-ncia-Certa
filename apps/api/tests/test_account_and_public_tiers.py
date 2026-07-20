from datetime import datetime, timedelta, timezone

from app.core.security import hash_password
from app.models.subscription import PaymentProvider, Subscription, SubscriptionStatus
from app.models.subscription_tier import BillingInterval, SubscriptionTier, TierCode
from app.models.user import User, UserRole, UserStatus


def _login(client, email: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": "supersecret"})
    return response.json()["access_token"]


def test_public_tiers_lists_only_active_tiers(client, db):
    active_tier = SubscriptionTier(
        code=TierCode.BASIC,
        name_i18n_key="tiers.basic.name",
        price_cents=1000,
        billing_interval=BillingInterval.MONTHLY,
        markets_allowed=["crypto"],
        is_active=True,
    )
    inactive_tier = SubscriptionTier(
        code=TierCode.VIP,
        name_i18n_key="tiers.vip.name",
        price_cents=9000,
        billing_interval=BillingInterval.MONTHLY,
        markets_allowed=["crypto", "forex", "b3"],
        is_active=False,
    )
    db.add_all([active_tier, inactive_tier])
    db.commit()

    response = client.get("/subscription-tiers")

    assert response.status_code == 200
    codes = [tier["code"] for tier in response.json()]
    assert codes == ["basic"]


def test_public_tiers_requires_no_authentication(client):
    response = client.get("/subscription-tiers")
    assert response.status_code == 200


def test_my_subscription_returns_no_active_subscription(client, db):
    user = User(
        email="nosub@example.com",
        password_hash=hash_password("supersecret"),
        name="No Sub",
        role=UserRole.SUBSCRIBER,
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    db.commit()

    token = _login(client, user.email)
    response = client.get("/me/subscription", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == {
        "has_active_subscription": False,
        "tier": None,
        "status": None,
        "current_period_end": None,
        "pending_tier": None,
    }


def test_my_subscription_returns_active_tier_and_pending_downgrade(client, db):
    user = User(
        email="withsub@example.com",
        password_hash=hash_password("supersecret"),
        name="With Sub",
        role=UserRole.SUBSCRIBER,
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    db.commit()

    vip_tier = SubscriptionTier(
        code=TierCode.VIP,
        name_i18n_key="tiers.vip.name",
        price_cents=9000,
        billing_interval=BillingInterval.MONTHLY,
        markets_allowed=["crypto", "forex", "b3"],
    )
    basic_tier = SubscriptionTier(
        code=TierCode.BASIC,
        name_i18n_key="tiers.basic.name",
        price_cents=1000,
        billing_interval=BillingInterval.MONTHLY,
        markets_allowed=["crypto"],
    )
    db.add_all([vip_tier, basic_tier])
    db.flush()

    period_end = datetime.now(timezone.utc) + timedelta(days=15)
    subscription = Subscription(
        user_id=user.id,
        tier_id=vip_tier.id,
        pending_tier_id=basic_tier.id,
        status=SubscriptionStatus.ACTIVE,
        payment_provider=PaymentProvider.STRIPE,
        current_period_start=datetime.now(timezone.utc) - timedelta(days=15),
        current_period_end=period_end,
    )
    db.add(subscription)
    db.commit()

    token = _login(client, user.email)
    response = client.get("/me/subscription", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["has_active_subscription"] is True
    assert body["tier"]["code"] == "vip"
    assert body["status"] == "active"
    assert body["pending_tier"]["code"] == "basic"


def test_my_subscription_requires_authentication(client):
    response = client.get("/me/subscription")
    assert response.status_code == 403
