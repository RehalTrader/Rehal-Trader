"""
Signal generator — the single function the backend calls (per symbol/timeframe, on
every new CLOSED candle) to produce one signal.

=== Non-repainting guarantee ===
1. This function must only ever be called with `df` whose LAST row is a fully closed
   candle (never the currently-forming one). Callers are responsible for this — e.g.
   the market-data feed marks candles `is_final=True` only after their period ends.
2. All features in `features/pipeline.py` are computed causally: every indicator at
   row i only looks at rows <= i (rolling windows, ewm, shifts — never `.shift(-1)`
   except inside `make_labels`, which is training-only and never used at inference).
3. Because of (1) and (2), a signal computed for candle_time=T will be bit-for-bit
   identical no matter when you compute it — now or a week from now — because no
   future data can leak in. Signals are persisted as INSERT-only rows (see
   backend/app/services/signal_service.py) so a signal is never silently changed
   after the fact — the "no repainting" contract clients see is enforced end-to-end.
"""
import logging

import pandas as pd

from features.pipeline import build_feature_matrix
from models.ensemble import SignalEnsemble
from models.lstm_model import LSTMSignalModel
from models.xgb_model import XGBSignalModel

logger = logging.getLogger(__name__)

ATR_STOP_MULTIPLIER = 1.5
ATR_TARGET_MULTIPLIER = 2.5


class SignalGenerator:
    def __init__(self):
        self.ensemble = SignalEnsemble(XGBSignalModel(), LSTMSignalModel())

    def generate(self, symbol: str, timeframe: str, candles: pd.DataFrame) -> dict:
        """
        candles: raw OHLCV DataFrame, ascending, LAST ROW MUST BE A CLOSED CANDLE.
        Returns a dict ready to persist as a Signal row.
        """
        features = build_feature_matrix(candles)
        if features.empty:
            raise ValueError("Not enough candles to compute features (need warm-up period).")

        latest = features.iloc[[-1]]
        direction, confidence = self.ensemble.score(snapshot_row=latest, sequence_window=features)

        entry_price = float(candles["close"].iloc[-1])
        atr_value = float(latest["atr"].iloc[0])

        if direction in ("STRONG_BUY", "BUY"):
            stop_loss = entry_price - ATR_STOP_MULTIPLIER * atr_value
            take_profit = entry_price + ATR_TARGET_MULTIPLIER * atr_value
        elif direction in ("STRONG_SELL", "SELL"):
            stop_loss = entry_price + ATR_STOP_MULTIPLIER * atr_value
            take_profit = entry_price - ATR_TARGET_MULTIPLIER * atr_value
        else:
            stop_loss = entry_price - ATR_STOP_MULTIPLIER * atr_value
            take_profit = entry_price + ATR_TARGET_MULTIPLIER * atr_value

        signal = {
            "symbol": symbol.upper(),
            "timeframe": timeframe,
            "direction": direction,
            "confidence": confidence,
            "entry_price": entry_price,
            "stop_loss": round(stop_loss, 5),
            "take_profit": round(take_profit, 5),
            "features": latest.iloc[0].to_dict(),
            "candle_time": candles.index[-1],
        }
        logger.info("Generated signal: %s %s %s conf=%.1f", symbol, timeframe, direction, confidence)
        return signal


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info(
        "signal_generator is a library module — import SignalGenerator from the backend "
        "or a scheduled worker rather than running this file directly in production."
    )
