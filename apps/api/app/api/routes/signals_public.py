from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_db
from app.models.asset import Asset
from app.models.signal import Signal, SignalStatus
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.user import User
from app.schemas.signal import SignalRead
from app.services.signal_visibility import SignalView, TierRules, filter_visible_signals

router = APIRouter(tags=["signals"])

ACTIVE_SUBSCRIPTION_STATUSES = (SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING)
CANDIDATE_STATUSES = (SignalStatus.ACTIVE, SignalStatus.HIT_TARGET, SignalStatus.HIT_STOP)


@router.get("/signals", response_model=list[SignalRead])
def list_signals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Signal]:
    subscription = (
        db.query(Subscription)
        .filter(
            Subscription.user_id == current_user.id,
            Subscription.status.in_(ACTIVE_SUBSCRIPTION_STATUSES),
        )
        .order_by(Subscription.created_at.desc())
        .first()
    )
    if subscription is None:
        return []

    tier = subscription.tier
    tier_rules = TierRules(
        code=tier.code.value,
        markets_allowed=tuple(tier.markets_allowed),
        signal_delay_minutes=tier.signal_delay_minutes,
        max_active_signals_visible=tier.max_active_signals_visible,
    )

    candidate_signals = (
        db.query(Signal)
        .options(joinedload(Signal.asset).joinedload(Asset.market), joinedload(Signal.targets))
        .filter(Signal.status.in_(CANDIDATE_STATUSES))
        .all()
    )

    now = datetime.now(timezone.utc)
    views = [
        SignalView(
            id=s.id,
            status=s.status.value,
            visibility_tier=s.visibility_tier.value,
            market_code=s.asset.market.code.value,
            published_at=s.published_at,
        )
        for s in candidate_signals
    ]

    visible_ids = [v.id for v in filter_visible_signals(views, tier_rules, now)]
    signals_by_id = {s.id: s for s in candidate_signals}
    return [signals_by_id[signal_id] for signal_id in visible_ids]
