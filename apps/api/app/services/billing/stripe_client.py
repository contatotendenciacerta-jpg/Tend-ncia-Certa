import stripe

from app.core.config import settings
from app.models.subscription_tier import BillingInterval, SubscriptionTier

stripe.api_key = settings.STRIPE_API_KEY

BILLING_INTERVAL_TO_STRIPE = {
    BillingInterval.MONTHLY: "month",
    BillingInterval.YEARLY: "year",
}


def create_checkout_session(
    *,
    customer_email: str,
    tier: SubscriptionTier,
    client_reference_id: str,
    metadata: dict[str, str],
    success_url: str,
    cancel_url: str,
):
    return stripe.checkout.Session.create(
        mode="subscription",
        customer_email=customer_email,
        client_reference_id=client_reference_id,
        line_items=[
            {
                "price_data": {
                    "currency": tier.currency.lower(),
                    "unit_amount": tier.price_cents,
                    "recurring": {"interval": BILLING_INTERVAL_TO_STRIPE[tier.billing_interval]},
                    "product_data": {"name": tier.name_i18n_key},
                },
                "quantity": 1,
            }
        ],
        metadata=metadata,
        success_url=success_url,
        cancel_url=cancel_url,
    )


def cancel_subscription(subscription_id: str) -> None:
    stripe.Subscription.delete(subscription_id)


def construct_webhook_event(payload: bytes, sig_header: str):
    return stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
