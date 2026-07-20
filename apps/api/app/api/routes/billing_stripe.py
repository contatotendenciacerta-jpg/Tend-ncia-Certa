import uuid

import stripe as stripe_sdk
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_stripe_configured
from app.core.config import settings
from app.models.subscription import PaymentProvider, Subscription
from app.models.subscription_tier import SubscriptionTier
from app.models.user import User
from app.schemas.billing import CheckoutRequest
from app.services.billing import stripe_client
from app.services.billing.subscription_service import (
    TierChangeDecision,
    activate_new_subscription,
    find_by_external_subscription_id,
    get_active_subscription,
    mark_canceled,
    mark_past_due,
    resolve_tier_change,
    schedule_downgrade,
)

router = APIRouter(prefix="/billing/stripe", tags=["billing:stripe"])


@router.post("/checkout-session", status_code=status.HTTP_201_CREATED)
def create_checkout_session(
    payload: CheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_stripe_configured),
) -> dict:
    tier = db.get(SubscriptionTier, payload.tier_id)
    if tier is None or not tier.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tier não encontrado")

    active_subscription = get_active_subscription(db, current_user.id)
    decision = resolve_tier_change(active_subscription, tier)

    if decision == TierChangeDecision.SAME:
        raise HTTPException(status.HTTP_409_CONFLICT, "Usuário já está inscrito neste tier")

    if decision == TierChangeDecision.DOWNGRADE:
        schedule_downgrade(db, active_subscription, tier)
        return {
            "scheduled_downgrade": True,
            "tier_id": str(tier.id),
            "effective_at": active_subscription.current_period_end.isoformat(),
        }

    metadata = {
        "user_id": str(current_user.id),
        "tier_id": str(tier.id),
        "upgrade_from_subscription_id": (
            str(active_subscription.id) if decision == TierChangeDecision.UPGRADE else ""
        ),
    }
    session = stripe_client.create_checkout_session(
        customer_email=current_user.email,
        tier=tier,
        client_reference_id=str(current_user.id),
        metadata=metadata,
        success_url=settings.STRIPE_SUCCESS_URL,
        cancel_url=settings.STRIPE_CANCEL_URL,
    )
    return {"checkout_url": session.url}


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(require_stripe_configured),
) -> dict:
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe_client.construct_webhook_event(payload, sig_header)
    except (stripe_sdk.error.SignatureVerificationError, ValueError) as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Assinatura inválida") from exc

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        _handle_checkout_completed(db, data)
    elif event_type == "invoice.payment_failed":
        _handle_invoice_payment_failed(db, data)
    elif event_type == "customer.subscription.deleted":
        _handle_subscription_deleted(db, data)

    return {"received": True}


def _handle_checkout_completed(db: Session, session: dict) -> None:
    metadata = session.get("metadata") or {}
    tier_id = metadata.get("tier_id")
    user_id = metadata.get("user_id")
    if not tier_id or not user_id:
        return

    tier = db.get(SubscriptionTier, uuid.UUID(tier_id))
    if tier is None:
        return

    upgrade_from = metadata.get("upgrade_from_subscription_id") or None
    cancel_row_id = uuid.UUID(upgrade_from) if upgrade_from else None

    if cancel_row_id is not None:
        old = db.get(Subscription, cancel_row_id)
        if old is not None and old.external_subscription_id:
            try:
                stripe_client.cancel_subscription(old.external_subscription_id)
            except Exception:
                pass

    activate_new_subscription(
        db,
        user_id=uuid.UUID(user_id),
        tier=tier,
        payment_provider=PaymentProvider.STRIPE,
        external_subscription_id=session.get("subscription"),
        amount_cents=session.get("amount_total") or tier.price_cents,
        currency=(session.get("currency") or tier.currency).upper(),
        provider_reference=session.get("id"),
        cancel_subscription_row_id=cancel_row_id,
    )


def _handle_invoice_payment_failed(db: Session, invoice: dict) -> None:
    external_subscription_id = invoice.get("subscription")
    if not external_subscription_id:
        return

    subscription = find_by_external_subscription_id(db, external_subscription_id)
    if subscription is None:
        return

    mark_past_due(
        db,
        subscription,
        amount_cents=invoice.get("amount_due"),
        currency=(invoice.get("currency") or subscription.tier.currency).upper(),
        provider_reference=invoice.get("id"),
    )


def _handle_subscription_deleted(db: Session, subscription_obj: dict) -> None:
    external_subscription_id = subscription_obj.get("id")
    if not external_subscription_id:
        return

    subscription = find_by_external_subscription_id(db, external_subscription_id)
    if subscription is None:
        return

    mark_canceled(db, subscription)
