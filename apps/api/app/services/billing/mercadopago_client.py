import hashlib
import hmac

import httpx

from app.core.config import settings
from app.models.subscription_tier import SubscriptionTier

BASE_URL = "https://api.mercadopago.com"


def create_preference(
    *,
    tier: SubscriptionTier,
    external_reference: str,
    success_url: str,
    failure_url: str,
    pending_url: str,
) -> dict:
    response = httpx.post(
        f"{BASE_URL}/checkout/preferences",
        headers={"Authorization": f"Bearer {settings.MERCADOPAGO_ACCESS_TOKEN}"},
        json={
            "items": [
                {
                    "title": tier.name_i18n_key,
                    "quantity": 1,
                    "unit_price": tier.price_cents / 100,
                    "currency_id": tier.currency,
                }
            ],
            "external_reference": external_reference,
            "back_urls": {"success": success_url, "failure": failure_url, "pending": pending_url},
            "auto_return": "approved",
        },
        timeout=10.0,
    )
    response.raise_for_status()
    return response.json()


def fetch_payment(payment_id: str) -> dict:
    response = httpx.get(
        f"{BASE_URL}/v1/payments/{payment_id}",
        headers={"Authorization": f"Bearer {settings.MERCADOPAGO_ACCESS_TOKEN}"},
        timeout=10.0,
    )
    response.raise_for_status()
    return response.json()


def verify_webhook_signature(*, x_signature: str, x_request_id: str, data_id: str, secret: str) -> bool:
    parts = dict(part.split("=", 1) for part in x_signature.split(",") if "=" in part)
    ts = parts.get("ts")
    received_hash = parts.get("v1")
    if not ts or not received_hash:
        return False

    # Manifest format per Mercado Pago's webhook signature docs: the data.id
    # from the callback query string, the x-request-id header, and the
    # timestamp from x-signature, joined with this exact template.
    manifest = f"id:{data_id.lower()};request-id:{x_request_id};ts:{ts};"
    expected_hash = hmac.new(secret.encode("utf-8"), manifest.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected_hash, received_hash)
