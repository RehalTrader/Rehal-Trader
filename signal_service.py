import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.redis_client import redis_client
from app.models.signal import Signal
from app.schemas.signal import SignalQuery
from app.services.notification_service import notify_all_channels

logger = logging.getLogger(__name__)


async def list_signals(db: AsyncSession, query: SignalQuery) -> list[Signal]:
    stmt = select(Signal).order_by(Signal.candle_time.desc())
    if query.symbol:
        stmt = stmt.where(Signal.symbol == query.symbol.upper())
    if query.asset_class:
        stmt = stmt.where(Signal.asset_class == query.asset_class)
    if query.timeframe:
        stmt = stmt.where(Signal.timeframe == query.timeframe)
    stmt = stmt.limit(query.limit).offset(query.offset)

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def persist_and_broadcast_signal(db: AsyncSession, signal: Signal) -> Signal:
    """
    Append-only insert (non-repainting: we never update an existing row),
    cache the latest value for the symbol, publish to the WS pub/sub channel,
    and fan out notifications (Telegram/email/push) for high-confidence signals.
    """
    db.add(signal)
    await db.commit()
    await db.refresh(signal)

    payload = {
        "id": str(signal.id),
        "symbol": signal.symbol,
        "asset_class": signal.asset_class.value,
        "timeframe": signal.timeframe,
        "direction": signal.direction.value,
        "confidence": signal.confidence,
        "entry_price": signal.entry_price,
        "stop_loss": signal.stop_loss,
        "take_profit": signal.take_profit,
        "candle_time": signal.candle_time.isoformat(),
    }

    await redis_client.set_json(f"latest_signal:{signal.symbol}", payload, ex=3600)
    await redis_client.publish_signal(payload)

    if signal.confidence >= 75 and signal.direction.value != "NEUTRAL":
        await notify_all_channels(payload)

    logger.info("Signal persisted: %s %s (%.1f%%)", signal.symbol, signal.direction.value, signal.confidence)
    return signal
