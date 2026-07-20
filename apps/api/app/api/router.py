from fastapi import APIRouter

from app.api.routes import (
    account,
    assets,
    auth,
    billing_mercadopago,
    billing_stripe,
    markets,
    signals_admin,
    signals_public,
    subscription_tiers,
    subscription_tiers_public,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(account.router)
api_router.include_router(markets.router)
api_router.include_router(assets.router)
api_router.include_router(subscription_tiers.router)
api_router.include_router(subscription_tiers_public.router)
api_router.include_router(signals_admin.router)
api_router.include_router(signals_public.router)
api_router.include_router(billing_stripe.router)
api_router.include_router(billing_mercadopago.router)
