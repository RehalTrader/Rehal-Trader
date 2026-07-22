from fastapi import APIRouter

from app.api.v1 import admin, auth, billing, market, signals, users, ws

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(signals.router)
api_router.include_router(market.router)
api_router.include_router(billing.router)
api_router.include_router(admin.router)

ws_router = APIRouter()
ws_router.include_router(ws.router)
