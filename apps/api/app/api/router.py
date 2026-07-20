from fastapi import APIRouter

from app.api.routes import assets, auth, markets, signals_admin, signals_public, subscription_tiers

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(markets.router)
api_router.include_router(assets.router)
api_router.include_router(subscription_tiers.router)
api_router.include_router(signals_admin.router)
api_router.include_router(signals_public.router)
