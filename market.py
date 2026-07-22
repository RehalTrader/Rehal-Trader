"""
Market data endpoints: supported symbols and the economic news calendar.

Note: `economic_news` below returns illustrative placeholder data. Wire `MARKET_DATA_PROVIDER`
/ a dedicated economic-calendar provider (e.g. ForexFactory-compatible feed, TradingEconomics,
FMP) here for real data — the endpoint shape (`NewsItem`) is designed to match a typical
calendar API response so swapping the data source doesn't require frontend changes.
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/market", tags=["market"])

SUPPORTED_SYMBOLS = {
    "forex": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"],
    "gold": ["XAUUSD"],
    "crypto": ["BTCUSD", "ETHUSD", "SOLUSD"],
    "indices": ["US30", "NAS100", "SPX500", "GER40"],
}


@router.get("/symbols")
async def get_symbols(_user: User = Depends(get_current_user)):
    return SUPPORTED_SYMBOLS


@router.get("/news")
async def economic_news(_user: User = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    return [
        {
            "time": (now + timedelta(hours=1)).strftime("%H:%M"),
            "currency": "USD",
            "impact": "high",
            "event": "Non-Farm Payrolls",
            "forecast": "180K",
            "previous": "175K",
        },
        {
            "time": (now + timedelta(hours=3)).strftime("%H:%M"),
            "currency": "EUR",
            "impact": "medium",
            "event": "ECB Rate Decision",
            "forecast": "3.75%",
            "previous": "3.75%",
        },
        {
            "time": (now + timedelta(hours=5)).strftime("%H:%M"),
            "currency": "GBP",
            "impact": "low",
            "event": "Retail Sales m/m",
            "forecast": "0.2%",
            "previous": "0.1%",
        },
    ]
