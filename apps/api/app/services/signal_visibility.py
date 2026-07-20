from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Hashable

VISIBLE_SIGNAL_STATUSES = {"active", "hit_target", "hit_stop"}

TIER_RANK = {"basic": 0, "pro": 1, "vip": 2}


@dataclass(frozen=True)
class SignalView:
    id: Hashable
    status: str
    visibility_tier: str
    market_code: str
    published_at: datetime | None


@dataclass(frozen=True)
class TierRules:
    code: str
    markets_allowed: tuple[str, ...]
    signal_delay_minutes: int
    max_active_signals_visible: int | None


def is_signal_visible(signal: SignalView, tier: TierRules, now: datetime) -> bool:
    if signal.status not in VISIBLE_SIGNAL_STATUSES:
        return False
    if signal.published_at is None:
        return False
    if TIER_RANK[signal.visibility_tier] > TIER_RANK[tier.code]:
        return False
    if signal.market_code not in tier.markets_allowed:
        return False
    effective_at = signal.published_at + timedelta(minutes=tier.signal_delay_minutes)
    return now >= effective_at


def filter_visible_signals(
    signals: list[SignalView], tier: TierRules, now: datetime
) -> list[SignalView]:
    visible = [s for s in signals if is_signal_visible(s, tier, now)]
    visible.sort(key=lambda s: s.published_at, reverse=True)
    if tier.max_active_signals_visible is not None:
        visible = visible[: tier.max_active_signals_visible]
    return visible
