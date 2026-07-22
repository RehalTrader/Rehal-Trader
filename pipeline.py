"""
Single entry point that turns raw OHLCV candles into the full feature matrix used by
both training and live inference. Keeping this in one function guarantees train/serve
parity — never hand-roll feature computation separately in two places.
"""
import pandas as pd

from features import indicators, sessions, smc


def build_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    df: raw candles with columns ['open','high','low','close','volume'], indexed by
        the candle's CLOSE time (UTC), ascending order, one row per *closed* candle only.
    Returns: df with all engineered feature columns appended (raw OHLCV columns kept too).
    """
    frames = [
        df,
        indicators.rsi(df).rename("rsi"),
        indicators.qqe(df),
        indicators.ema_trend(df),
        indicators.atr(df).rename("atr"),
        indicators.macd(df),
        indicators.bollinger_bands(df),
        indicators.volume_features(df),
        indicators.support_resistance(df),
        smc.break_of_structure(df),
        smc.change_of_character(df),
        smc.fair_value_gap(df),
        smc.liquidity_sweep(df),
        sessions.market_sessions(df),
    ]
    features = pd.concat(frames, axis=1)

    # Drop the warm-up rows where rolling windows aren't fully populated yet
    return features.dropna().copy()


FEATURE_COLUMNS = [
    "rsi", "qqe_rsi_ma", "qqe_trend",
    "ema_fast", "ema_slow", "ema_macro", "trend_score",
    "atr",
    "macd", "macd_signal", "macd_hist",
    "bb_percent_b",
    "volume_ratio", "volume_zscore",
    "near_resistance", "near_support",
    "bos_bullish", "bos_bearish",
    "choch_bullish", "choch_bearish",
    "fvg_bullish", "fvg_bearish", "fvg_size",
    "liquidity_sweep_high", "liquidity_sweep_low",
    "session_sydney", "session_tokyo", "session_london", "session_new_york", "session_london_ny_overlap",
]
