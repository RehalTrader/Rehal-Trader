import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.signal import AssetClass, SignalDirection


class SignalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    symbol: str
    asset_class: AssetClass
    timeframe: str
    direction: SignalDirection
    confidence: float
    entry_price: float
    stop_loss: float
    take_profit: float
    candle_time: datetime
    created_at: datetime


class SignalQuery(BaseModel):
    symbol: str | None = None
    asset_class: AssetClass | None = None
    timeframe: str | None = None
    limit: int = 50
    offset: int = 0
