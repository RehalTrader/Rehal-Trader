from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.signal import AssetClass
from app.models.user import User
from app.schemas.signal import SignalOut, SignalQuery
from app.services.signal_service import list_signals

router = APIRouter(prefix="/signals", tags=["signals"])


@router.get("/", response_model=list[SignalOut])
async def get_signals(
    symbol: str | None = Query(default=None),
    asset_class: AssetClass | None = Query(default=None),
    timeframe: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Signal history for the dashboard. Free-plan users are limited server-side
    (see subscription enforcement middleware) to delayed / limited symbols."""
    query = SignalQuery(symbol=symbol, asset_class=asset_class, timeframe=timeframe, limit=limit, offset=offset)
    return await list_signals(db, query)
