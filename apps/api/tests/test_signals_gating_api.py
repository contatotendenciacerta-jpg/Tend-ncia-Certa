from datetime import datetime, timedelta, timezone

from app.core.security import hash_password
from app.models.asset import Asset
from app.models.market import Market, MarketCode
from app.models.signal import (
    ConfidenceLevel,
    Signal,
    SignalDirection,
    SignalSource,
    SignalStatus,
    SignalTimeframe,
    SignalVisibilityTier,
)
from app.models.subscription import PaymentProvider, Subscription, SubscriptionStatus
from app.models.subscription_tier import BillingInterval, SubscriptionTier, TierCode
from app.models.user import User, UserRole, UserStatus


def _create_crypto_asset(db) -> Asset:
    market = Market(code=MarketCode.CRYPTO, name_i18n_key="markets.crypto.name")
    db.add(market)
    db.flush()
    asset = Asset(market_id=market.id, symbol="BTCUSDT", display_name="BTC/USDT")
    db.add(asset)
    db.commit()
    return asset


def _create_subscriber_with_tier(
    db, tier_code: TierCode, markets_allowed: list[str], delay_minutes: int, max_visible: int | None = None
) -> User:
    tier = SubscriptionTier(
        code=tier_code,
        name_i18n_key=f"tiers.{tier_code.value}.name",
        price_cents=1000,
        billing_interval=BillingInterval.MONTHLY,
        markets_allowed=markets_allowed,
        signal_delay_minutes=delay_minutes,
        max_active_signals_visible=max_visible,
    )
    db.add(tier)
    db.flush()

    user = User(
        email=f"{tier_code.value}@example.com",
        password_hash=hash_password("supersecret"),
        name="Test User",
        role=UserRole.SUBSCRIBER,
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    db.flush()

    subscription = Subscription(
        user_id=user.id,
        tier_id=tier.id,
        status=SubscriptionStatus.ACTIVE,
        payment_provider=PaymentProvider.STRIPE,
        current_period_start=datetime.now(timezone.utc) - timedelta(days=1),
        current_period_end=datetime.now(timezone.utc) + timedelta(days=29),
    )
    db.add(subscription)
    db.commit()
    return user


def _create_signal(
    db,
    asset: Asset,
    visibility_tier: SignalVisibilityTier,
    published_minutes_ago: float,
    status: SignalStatus = SignalStatus.ACTIVE,
) -> Signal:
    signal = Signal(
        asset_id=asset.id,
        direction=SignalDirection.BUY,
        entry_price="100.00",
        stop_loss="90.00",
        timeframe=SignalTimeframe.H1,
        confidence_level=ConfidenceLevel.HIGH,
        source=SignalSource.ALGORITHM,
        algorithm_name="test-bot",
        visibility_tier=visibility_tier,
        status=status,
        published_at=datetime.now(timezone.utc) - timedelta(minutes=published_minutes_ago),
    )
    db.add(signal)
    db.commit()
    return signal


def _login(client, email: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": "supersecret"})
    return response.json()["access_token"]


def test_basic_user_does_not_see_vip_signal(client, db):
    asset = _create_crypto_asset(db)
    user = _create_subscriber_with_tier(db, TierCode.BASIC, ["crypto"], delay_minutes=30, max_visible=5)
    _create_signal(db, asset, SignalVisibilityTier.VIP, published_minutes_ago=120)

    token = _login(client, user.email)
    response = client.get("/signals", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == []


def test_basic_user_sees_basic_signal_after_delay(client, db):
    asset = _create_crypto_asset(db)
    user = _create_subscriber_with_tier(db, TierCode.BASIC, ["crypto"], delay_minutes=30, max_visible=5)
    _create_signal(db, asset, SignalVisibilityTier.BASIC, published_minutes_ago=60)

    token = _login(client, user.email)
    response = client.get("/signals", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_basic_user_does_not_see_signal_still_in_delay_window(client, db):
    asset = _create_crypto_asset(db)
    user = _create_subscriber_with_tier(db, TierCode.BASIC, ["crypto"], delay_minutes=30, max_visible=5)
    _create_signal(db, asset, SignalVisibilityTier.BASIC, published_minutes_ago=10)

    token = _login(client, user.email)
    response = client.get("/signals", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == []


def test_pro_user_sees_signal_immediately_no_delay(client, db):
    asset = _create_crypto_asset(db)
    user = _create_subscriber_with_tier(db, TierCode.PRO, ["crypto", "forex", "b3"], delay_minutes=0)
    _create_signal(db, asset, SignalVisibilityTier.PRO, published_minutes_ago=0.01)

    token = _login(client, user.email)
    response = client.get("/signals", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_user_without_active_subscription_sees_nothing(client, db):
    asset = _create_crypto_asset(db)
    _create_signal(db, asset, SignalVisibilityTier.BASIC, published_minutes_ago=120)

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
    response = client.get("/signals", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == []


def test_pending_signal_is_never_returned_even_for_vip(client, db):
    asset = _create_crypto_asset(db)
    user = _create_subscriber_with_tier(db, TierCode.VIP, ["crypto", "forex", "b3"], delay_minutes=0)
    _create_signal(
        db, asset, SignalVisibilityTier.VIP, published_minutes_ago=60, status=SignalStatus.PENDING
    )

    token = _login(client, user.email)
    response = client.get("/signals", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == []
