import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_mercadopago_configured
from app.core.config import settings
from app.models.subscription import PaymentProvider, Subscription
from app.models.subscription_tier import SubscriptionTier
from app.models.user import User
from app.schemas.billing import CheckoutRequest
from app.services.billing import mercadopago_client
from app.services.billing.subscription_service import (
    TierChangeDecision,
    activate_new_subscription,
    get_active_subscription,
    mark_canceled,
    mark_past_due,
    renew_or_upgrade_subscription,
    resolve_tier_change,
    schedule_downgrade,
)

router = APIRouter(prefix="/billing/mercadopago", tags=["billing:mercadopago"])

APPROVED_STATUSES = {"approved"}
REJECTED_STATUSES = {"rejected"}
CANCELED_STATUSES = {"cancelled"}


@router.post("/preference", status_code=status.HTTP_201_CREATED)
def create_preference(
    payload: CheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_mercadopago_configured),
) -> dict:
    tier = db.get(SubscriptionTier, payload.tier_id)
    if tier is None or not tier.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tier não encontrado")

    active_subscription = get_active_subscription(db, current_user.id)
    decision = resolve_tier_change(active_subscription, tier)

    if decision == TierChangeDecision.DOWNGRADE:
        schedule_downgrade(db, active_subscription, tier)
        return {
            "scheduled_downgrade": True,
            "tier_id": str(tier.id),
            "effective_at": active_subscription.current_period_end.isoformat(),
        }

    external_reference = json.dumps(
        {
            "user_id": str(current_user.id),
            "tier_id": str(tier.id),
            "subscription_id": str(active_subscription.id) if active_subscription else None,
        }
    )

    preference = mercadopago_client.create_preference(
        tier=tier,
        external_reference=external_reference,
        success_url=settings.MERCADOPAGO_SUCCESS_URL,
        failure_url=settings.MERCADOPAGO_FAILURE_URL,
        pending_url=settings.MERCADOPAGO_PENDING_URL,
    )
    return {"checkout_url": preference["init_point"], "preference_id": preference["id"]}


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def mercadopago_webhook(
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(require_mercadopago_configured),
) -> dict:
    query_params = request.query_params
    raw_body = await request.body()
    body = {}
    if raw_body:
        try:
            body = json.loads(raw_body)
        except ValueError:
            body = {}

    notification_type = query_params.get("type") or body.get("type")
    data_id = query_params.get("data.id") or (body.get("data") or {}).get("id")

    if notification_type != "payment" or not data_id:
        return {"received": True}

    x_signature = request.headers.get("x-signature", "")
    x_request_id = request.headers.get("x-request-id", "")
    if not mercadopago_client.verify_webhook_signature(
        x_signature=x_signature,
        x_request_id=x_request_id,
        data_id=str(data_id),
        secret=settings.MERCADOPAGO_WEBHOOK_SECRET,
    ):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Assinatura inválida")

    payment = mercadopago_client.fetch_payment(str(data_id))
    _handle_payment_notification(db, payment)

    return {"received": True}


def _handle_payment_notification(db: Session, payment: dict) -> None:
    external_reference = payment.get("external_reference")
    if not external_reference:
        return

    try:
        reference = json.loads(external_reference)
    except ValueError:
        return

    tier_id = reference.get("tier_id")
    user_id = reference.get("user_id")
    existing_subscription_id = reference.get("subscription_id")
    if tier_id is None or user_id is None:
        return

    tier = db.get(SubscriptionTier, uuid.UUID(tier_id))
    if tier is None:
        return

    payment_status = payment.get("status")
    amount_cents = round(float(payment.get("transaction_amount", 0)) * 100)
    currency = (payment.get("currency_id") or tier.currency).upper()
    provider_reference = str(payment.get("id"))

    existing_subscription = (
        db.get(Subscription, uuid.UUID(existing_subscription_id)) if existing_subscription_id else None
    )

    if payment_status in APPROVED_STATUSES:
        if existing_subscription is not None:
            renew_or_upgrade_subscription(
                db,
                subscription=existing_subscription,
                tier=tier,
                amount_cents=amount_cents,
                currency=currency,
                provider_reference=provider_reference,
            )
        else:
            activate_new_subscription(
                db,
                user_id=uuid.UUID(user_id),
                tier=tier,
                payment_provider=PaymentProvider.MERCADOPAGO,
                external_subscription_id=None,
                amount_cents=amount_cents,
                currency=currency,
                provider_reference=provider_reference,
            )
    elif payment_status in REJECTED_STATUSES and existing_subscription is not None:
        mark_past_due(
            db,
            existing_subscription,
            amount_cents=amount_cents,
            currency=currency,
            provider_reference=provider_reference,
        )
    elif payment_status in CANCELED_STATUSES and existing_subscription is not None:
        mark_canceled(db, existing_subscription)
    # pending/in_process/etc: payment not yet confirmed, no subscription state change
