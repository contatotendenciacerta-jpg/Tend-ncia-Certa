"""Seeds demo data: tiers, a crypto market/assets, an admin user, a
subscriber with an active Pro subscription, and two sample signals.

Safe to run more than once - skips creation of anything that already
exists (matched by tier code, market code, asset symbol, user email).

Usage:
    python scripts/seed_demo_data.py

Reads DATABASE_URL from the environment the same way the app does. Admin
and demo passwords can be overridden via SEED_ADMIN_PASSWORD /
SEED_DEMO_PASSWORD env vars - change them after the first login.
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.security import hash_password
from app.db.session import SessionLocal
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
from app.models.signal_target import SignalTarget
from app.models.subscription import PaymentProvider, Subscription, SubscriptionStatus
from app.models.subscription_tier import BillingInterval, SubscriptionTier, TierCode
from app.models.user import User, UserRole, UserStatus

ADMIN_EMAIL = "admin@tendenciacerta.com"
DEMO_EMAIL = "demo@tendenciacerta.com"
ADMIN_PASSWORD = os.environ.get("SEED_ADMIN_PASSWORD", "admin12345")
DEMO_PASSWORD = os.environ.get("SEED_DEMO_PASSWORD", "demo12345")


def get_or_create_tier(db, code: TierCode, **kwargs) -> SubscriptionTier:
    tier = db.query(SubscriptionTier).filter(SubscriptionTier.code == code).first()
    if tier is not None:
        return tier
    tier = SubscriptionTier(code=code, **kwargs)
    db.add(tier)
    db.flush()
    return tier


def get_or_create_market(db, code: MarketCode, name_i18n_key: str) -> Market:
    market = db.query(Market).filter(Market.code == code).first()
    if market is not None:
        return market
    market = Market(code=code, name_i18n_key=name_i18n_key)
    db.add(market)
    db.flush()
    return market


def get_or_create_asset(db, market: Market, symbol: str, display_name: str) -> Asset:
    asset = db.query(Asset).filter(Asset.market_id == market.id, Asset.symbol == symbol).first()
    if asset is not None:
        return asset
    asset = Asset(market_id=market.id, symbol=symbol, display_name=display_name)
    db.add(asset)
    db.flush()
    return asset


def get_or_create_user(db, email: str, password: str, name: str, role: UserRole) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user is not None:
        return user
    user = User(
        email=email, password_hash=hash_password(password), name=name, role=role, status=UserStatus.ACTIVE
    )
    db.add(user)
    db.flush()
    return user


def main() -> None:
    db = SessionLocal()

    get_or_create_tier(
        db,
        TierCode.BASIC,
        name_i18n_key="tiers.basic.name",
        price_cents=4990,
        billing_interval=BillingInterval.MONTHLY,
        markets_allowed=["crypto"],
        signal_delay_minutes=30,
        max_active_signals_visible=5,
    )
    pro = get_or_create_tier(
        db,
        TierCode.PRO,
        name_i18n_key="tiers.pro.name",
        price_cents=14990,
        billing_interval=BillingInterval.MONTHLY,
        markets_allowed=["crypto", "forex", "b3"],
        signal_delay_minutes=0,
        max_active_signals_visible=None,
        push_notifications=True,
    )
    get_or_create_tier(
        db,
        TierCode.VIP,
        name_i18n_key="tiers.vip.name",
        price_cents=39990,
        billing_interval=BillingInterval.MONTHLY,
        markets_allowed=["crypto", "forex", "b3"],
        signal_delay_minutes=0,
        max_active_signals_visible=None,
        push_notifications=True,
        allows_vip_only_signals=True,
    )

    market = get_or_create_market(db, MarketCode.CRYPTO, "markets.crypto.name")
    btc = get_or_create_asset(db, market, "BTCUSDT", "Bitcoin / USDT")
    eth = get_or_create_asset(db, market, "ETHUSDT", "Ethereum / USDT")

    admin = get_or_create_user(db, ADMIN_EMAIL, ADMIN_PASSWORD, "Admin", UserRole.ADMIN)
    demo = get_or_create_user(db, DEMO_EMAIL, DEMO_PASSWORD, "Demo User", UserRole.SUBSCRIBER)

    existing_subscription = (
        db.query(Subscription)
        .filter(Subscription.user_id == demo.id, Subscription.status == SubscriptionStatus.ACTIVE)
        .first()
    )
    if existing_subscription is None:
        db.add(
            Subscription(
                user_id=demo.id,
                tier_id=pro.id,
                status=SubscriptionStatus.ACTIVE,
                payment_provider=PaymentProvider.STRIPE,
                external_subscription_id="sub_demo_seed",
                current_period_start=datetime.now(timezone.utc) - timedelta(days=2),
                current_period_end=datetime.now(timezone.utc) + timedelta(days=28),
            )
        )
        db.flush()

    if db.query(Signal).filter(Signal.asset_id == btc.id).first() is None:
        signal = Signal(
            asset_id=btc.id,
            direction=SignalDirection.BUY,
            entry_price="67250.50",
            stop_loss="65800.00",
            timeframe=SignalTimeframe.H4,
            confidence_level=ConfidenceLevel.HIGH,
            source=SignalSource.ALGORITHM,
            algorithm_name="trend-bot-v2",
            visibility_tier=SignalVisibilityTier.BASIC,
            status=SignalStatus.ACTIVE,
            published_at=datetime.now(timezone.utc) - timedelta(hours=2),
        )
        signal.targets = [
            SignalTarget(order=1, target_price="69000.00"),
            SignalTarget(order=2, target_price="71500.00"),
        ]
        db.add(signal)

    if db.query(Signal).filter(Signal.asset_id == eth.id).first() is None:
        signal = Signal(
            asset_id=eth.id,
            direction=SignalDirection.SELL,
            entry_price="3450.00",
            stop_loss="3520.00",
            timeframe=SignalTimeframe.H1,
            confidence_level=ConfidenceLevel.MEDIUM,
            source=SignalSource.MANUAL,
            created_by_admin_id=admin.id,
            visibility_tier=SignalVisibilityTier.PRO,
            status=SignalStatus.ACTIVE,
            published_at=datetime.now(timezone.utc) - timedelta(minutes=20),
        )
        signal.targets = [SignalTarget(order=1, target_price="3350.00")]
        db.add(signal)

    db.commit()

    print("Seed complete.")
    print(f"  Admin login:  {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
    print(f"  Demo login:   {DEMO_EMAIL} / {DEMO_PASSWORD}")
    print("  Change both passwords once you've confirmed access.")


if __name__ == "__main__":
    main()
