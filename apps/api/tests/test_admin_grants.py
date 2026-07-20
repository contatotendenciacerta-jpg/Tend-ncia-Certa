import uuid
from datetime import datetime, timedelta, timezone

from app.core.security import hash_password
from app.models.payment import Payment
from app.models.subscription import PaymentProvider, Subscription, SubscriptionStatus
from app.models.subscription_tier import BillingInterval, SubscriptionTier, TierCode
from app.models.user import User, UserRole, UserStatus


def _create_admin(db) -> User:
    admin = User(
        email="grant-admin@example.com",
        password_hash=hash_password("supersecret"),
        name="Admin",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
    )
    db.add(admin)
    db.commit()
    return admin


def _create_subscriber(db, email: str = "grant-subscriber@example.com") -> User:
    user = User(
        email=email,
        password_hash=hash_password("supersecret"),
        name="Subscriber",
        role=UserRole.SUBSCRIBER,
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    db.commit()
    return user


def _create_tier(db, code: TierCode = TierCode.PRO) -> SubscriptionTier:
    tier = SubscriptionTier(
        code=code,
        name_i18n_key=f"tiers.{code.value}.name",
        price_cents=5000,
        billing_interval=BillingInterval.MONTHLY,
        markets_allowed=["crypto"],
    )
    db.add(tier)
    db.commit()
    return tier


def _login(client, email: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": "supersecret"})
    return response.json()["access_token"]


def test_admin_can_grant_subscription(client, db):
    admin = _create_admin(db)
    user = _create_subscriber(db)
    tier = _create_tier(db)
    token = _login(client, admin.email)

    response = client.post(
        f"/admin/users/{user.id}/grant-subscription",
        json={"tier_id": str(tier.id), "duration_days": 14},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["user_id"] == str(user.id)
    assert body["tier_id"] == str(tier.id)
    assert body["status"] == "active"
    assert body["payment_provider"] == "manual"

    subscription = db.query(Subscription).filter(Subscription.user_id == user.id).one()
    assert subscription.payment_provider == PaymentProvider.MANUAL
    assert subscription.status == SubscriptionStatus.ACTIVE
    period_days = (subscription.current_period_end - subscription.current_period_start).days
    assert period_days == 14

    # A manual grant is not a real payment - no Payment row should exist.
    assert db.query(Payment).filter(Payment.subscription_id == subscription.id).count() == 0


def test_grant_subscription_defaults_to_30_days(client, db):
    admin = _create_admin(db)
    user = _create_subscriber(db, email="default-days@example.com")
    tier = _create_tier(db)
    token = _login(client, admin.email)

    response = client.post(
        f"/admin/users/{user.id}/grant-subscription",
        json={"tier_id": str(tier.id)},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    subscription = db.query(Subscription).filter(Subscription.user_id == user.id).one()
    period_days = (subscription.current_period_end - subscription.current_period_start).days
    assert period_days == 30


def test_grant_subscription_replaces_existing_active_one(client, db):
    admin = _create_admin(db)
    user = _create_subscriber(db, email="replace@example.com")
    basic_tier = _create_tier(db, TierCode.BASIC)
    vip_tier = _create_tier(db, TierCode.VIP)
    token = _login(client, admin.email)

    old_subscription = Subscription(
        user_id=user.id,
        tier_id=basic_tier.id,
        status=SubscriptionStatus.ACTIVE,
        payment_provider=PaymentProvider.STRIPE,
        current_period_start=datetime.now(timezone.utc) - timedelta(days=1),
        current_period_end=datetime.now(timezone.utc) + timedelta(days=29),
    )
    db.add(old_subscription)
    db.commit()

    response = client.post(
        f"/admin/users/{user.id}/grant-subscription",
        json={"tier_id": str(vip_tier.id), "duration_days": 7},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    db.refresh(old_subscription)
    assert old_subscription.status == SubscriptionStatus.CANCELED

    new_subscription = (
        db.query(Subscription)
        .filter(Subscription.user_id == user.id, Subscription.status == SubscriptionStatus.ACTIVE)
        .one()
    )
    assert new_subscription.tier_id == vip_tier.id


def test_grant_subscription_rejects_non_admin(client, db):
    user = _create_subscriber(db, email="notadmin@example.com")
    tier = _create_tier(db)
    token = _login(client, user.email)

    response = client.post(
        f"/admin/users/{user.id}/grant-subscription",
        json={"tier_id": str(tier.id)},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_grant_subscription_404s_for_unknown_user(client, db):
    admin = _create_admin(db)
    tier = _create_tier(db)
    token = _login(client, admin.email)

    response = client.post(
        f"/admin/users/{uuid.uuid4()}/grant-subscription",
        json={"tier_id": str(tier.id)},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


def test_grant_subscription_404s_for_unknown_tier(client, db):
    admin = _create_admin(db)
    user = _create_subscriber(db, email="unknown-tier@example.com")
    token = _login(client, admin.email)

    response = client.post(
        f"/admin/users/{user.id}/grant-subscription",
        json={"tier_id": str(uuid.uuid4())},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
