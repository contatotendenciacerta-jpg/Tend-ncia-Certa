from datetime import datetime, timedelta, timezone

from app.services.signal_visibility import (
    SignalView,
    TierRules,
    filter_visible_signals,
    is_signal_visible,
)

NOW = datetime(2026, 7, 20, 12, 0, tzinfo=timezone.utc)

BASIC_TIER = TierRules(
    code="basic", markets_allowed=("crypto",), signal_delay_minutes=30, max_active_signals_visible=5
)
PRO_TIER = TierRules(
    code="pro",
    markets_allowed=("crypto", "forex", "b3"),
    signal_delay_minutes=0,
    max_active_signals_visible=None,
)
VIP_TIER = TierRules(
    code="vip",
    markets_allowed=("crypto", "forex", "b3"),
    signal_delay_minutes=0,
    max_active_signals_visible=None,
)


def make_signal(**overrides) -> SignalView:
    defaults = dict(
        id=1,
        status="active",
        visibility_tier="basic",
        market_code="crypto",
        published_at=NOW - timedelta(minutes=60),
    )
    defaults.update(overrides)
    return SignalView(**defaults)


def test_basic_tier_does_not_see_vip_signal():
    signal = make_signal(visibility_tier="vip")
    assert is_signal_visible(signal, BASIC_TIER, NOW) is False


def test_basic_tier_does_not_see_pro_signal():
    signal = make_signal(visibility_tier="pro")
    assert is_signal_visible(signal, BASIC_TIER, NOW) is False


def test_pro_tier_does_not_see_vip_signal():
    signal = make_signal(visibility_tier="vip")
    assert is_signal_visible(signal, PRO_TIER, NOW) is False


def test_vip_tier_sees_basic_signal():
    signal = make_signal(visibility_tier="basic")
    assert is_signal_visible(signal, VIP_TIER, NOW) is True


def test_vip_tier_sees_own_tier_signal():
    signal = make_signal(visibility_tier="vip")
    assert is_signal_visible(signal, VIP_TIER, NOW) is True


def test_basic_tier_blocked_by_market_not_allowed():
    signal = make_signal(market_code="forex", visibility_tier="basic")
    assert is_signal_visible(signal, BASIC_TIER, NOW) is False


def test_pro_tier_sees_forex_signal():
    signal = make_signal(market_code="forex", visibility_tier="pro")
    assert is_signal_visible(signal, PRO_TIER, NOW) is True


def test_signal_hidden_before_delay_elapses():
    signal = make_signal(published_at=NOW - timedelta(minutes=10))  # basic delay is 30min
    assert is_signal_visible(signal, BASIC_TIER, NOW) is False


def test_signal_visible_exactly_at_delay_boundary():
    signal = make_signal(published_at=NOW - timedelta(minutes=30))
    assert is_signal_visible(signal, BASIC_TIER, NOW) is True


def test_signal_visible_after_delay_elapses():
    signal = make_signal(published_at=NOW - timedelta(minutes=31))
    assert is_signal_visible(signal, BASIC_TIER, NOW) is True


def test_signal_visible_immediately_for_zero_delay_tier():
    signal = make_signal(published_at=NOW, visibility_tier="pro")
    assert is_signal_visible(signal, PRO_TIER, NOW) is True


def test_pending_signal_not_visible():
    signal = make_signal(status="pending")
    assert is_signal_visible(signal, VIP_TIER, NOW) is False


def test_canceled_signal_not_visible():
    signal = make_signal(status="canceled")
    assert is_signal_visible(signal, VIP_TIER, NOW) is False


def test_expired_signal_not_visible():
    signal = make_signal(status="expired")
    assert is_signal_visible(signal, VIP_TIER, NOW) is False


def test_hit_target_signal_is_visible():
    signal = make_signal(status="hit_target")
    assert is_signal_visible(signal, VIP_TIER, NOW) is True


def test_signal_without_published_at_not_visible():
    signal = make_signal(published_at=None)
    assert is_signal_visible(signal, VIP_TIER, NOW) is False


def test_filter_respects_max_visible_limit():
    signals = [make_signal(id=i, published_at=NOW - timedelta(minutes=40 + i)) for i in range(10)]
    result = filter_visible_signals(signals, BASIC_TIER, NOW)
    assert len(result) == 5
    assert result[0].id == 0  # most recently published


def test_filter_orders_most_recent_first():
    older = make_signal(id="older", published_at=NOW - timedelta(minutes=100))
    newer = make_signal(id="newer", published_at=NOW - timedelta(minutes=40))
    result = filter_visible_signals([older, newer], BASIC_TIER, NOW)
    assert [s.id for s in result] == ["newer", "older"]


def test_filter_excludes_signals_from_other_tiers_and_markets():
    signals = [
        make_signal(id="ok", visibility_tier="basic", market_code="crypto"),
        make_signal(id="wrong-tier", visibility_tier="vip", market_code="crypto"),
        make_signal(id="wrong-market", visibility_tier="basic", market_code="forex"),
    ]
    result = filter_visible_signals(signals, BASIC_TIER, NOW)
    assert [s.id for s in result] == ["ok"]
