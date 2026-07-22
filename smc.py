"""
Smart Money Concept (SMC) / price-action structure features:
  - Break of Structure (BOS)
  - Change of Character (CHOCH)
  - Fair Value Gap (FVG)
  - Liquidity Sweep

These are rule-based structural detectors (not ML) that feed engineered boolean/
numeric columns into the model — the model learns how much weight to give each one
rather than us hardcoding trade rules.
"""
import numpy as np
import pandas as pd


def _swing_points(df: pd.DataFrame, order: int = 3) -> pd.DataFrame:
    """
    Local swing highs/lows: a candle is a swing high if its high is the max within
    +/- `order` candles (and swing low analogously). Returns boolean columns.
    """
    highs, lows = df["high"].values, df["low"].values
    n = len(df)
    swing_high = np.zeros(n, dtype=bool)
    swing_low = np.zeros(n, dtype=bool)

    for i in range(order, n - order):
        window_high = highs[i - order : i + order + 1]
        window_low = lows[i - order : i + order + 1]
        if highs[i] == window_high.max():
            swing_high[i] = True
        if lows[i] == window_low.min():
            swing_low[i] = True

    return pd.DataFrame({"swing_high": swing_high, "swing_low": swing_low}, index=df.index)


def break_of_structure(df: pd.DataFrame, order: int = 3) -> pd.DataFrame:
    """
    BOS: price closes beyond the most recent confirmed swing high (bullish BOS) or
    swing low (bearish BOS) *in the direction of the existing trend* — a continuation signal.
    """
    swings = _swing_points(df, order)
    last_swing_high, last_swing_low = np.nan, np.nan
    bos_bullish = np.zeros(len(df), dtype=bool)
    bos_bearish = np.zeros(len(df), dtype=bool)

    highs, lows, closes = df["high"].values, df["low"].values, df["close"].values

    for i in range(len(df)):
        if swings["swing_high"].iloc[i]:
            last_swing_high = highs[i]
        if swings["swing_low"].iloc[i]:
            last_swing_low = lows[i]

        if not np.isnan(last_swing_high) and closes[i] > last_swing_high:
            bos_bullish[i] = True
        if not np.isnan(last_swing_low) and closes[i] < last_swing_low:
            bos_bearish[i] = True

    return pd.DataFrame({"bos_bullish": bos_bullish.astype(int), "bos_bearish": bos_bearish.astype(int)}, index=df.index)


def change_of_character(df: pd.DataFrame, order: int = 3) -> pd.DataFrame:
    """
    CHOCH: the *first* break of structure in the opposite direction of the prevailing
    trend — signals a potential trend reversal (as distinct from BOS, which confirms
    continuation). Implemented as: previous N bars trended one way (via swing sequence),
    then price breaks structure the other way.
    """
    bos = break_of_structure(df, order)
    trend = np.where(bos["bos_bullish"].cumsum() > bos["bos_bearish"].cumsum(), 1, -1)

    choch_bullish = np.zeros(len(df), dtype=int)
    choch_bearish = np.zeros(len(df), dtype=int)

    for i in range(1, len(df)):
        if trend[i - 1] == -1 and bos["bos_bullish"].iloc[i] == 1:
            choch_bullish[i] = 1
        if trend[i - 1] == 1 and bos["bos_bearish"].iloc[i] == 1:
            choch_bearish[i] = 1

    return pd.DataFrame({"choch_bullish": choch_bullish, "choch_bearish": choch_bearish}, index=df.index)


def fair_value_gap(df: pd.DataFrame) -> pd.DataFrame:
    """
    3-candle imbalance: bullish FVG when candle[i-2].high < candle[i].low (a gap the
    market hasn't traded through yet); bearish FVG the mirror image. Also reports the
    gap size normalized by ATR-like range for the model to weigh gap significance.
    """
    high, low = df["high"].values, df["low"].values
    n = len(df)
    bullish_fvg = np.zeros(n, dtype=int)
    bearish_fvg = np.zeros(n, dtype=int)
    gap_size = np.zeros(n, dtype=float)

    for i in range(2, n):
        if low[i] > high[i - 2]:
            bullish_fvg[i] = 1
            gap_size[i] = low[i] - high[i - 2]
        elif high[i] < low[i - 2]:
            bearish_fvg[i] = 1
            gap_size[i] = low[i - 2] - high[i]

    return pd.DataFrame(
        {"fvg_bullish": bullish_fvg, "fvg_bearish": bearish_fvg, "fvg_size": gap_size}, index=df.index
    )


def liquidity_sweep(df: pd.DataFrame, order: int = 3, wick_ratio: float = 0.6) -> pd.DataFrame:
    """
    A liquidity sweep: price wicks beyond a recent swing high/low (grabbing stop-loss
    liquidity) then closes back inside the prior range — a classic stop-hunt pattern
    that often precedes a reversal.
    """
    swings = _swing_points(df, order)
    high, low, close, open_ = df["high"].values, df["low"].values, df["close"].values, df["open"].values
    n = len(df)

    sweep_high = np.zeros(n, dtype=int)   # swept buy-side liquidity -> bearish signal
    sweep_low = np.zeros(n, dtype=int)    # swept sell-side liquidity -> bullish signal

    last_swing_high, last_swing_low = np.nan, np.nan
    for i in range(n):
        if swings["swing_high"].iloc[i]:
            last_swing_high = high[i]
        if swings["swing_low"].iloc[i]:
            last_swing_low = low[i]

        candle_range = max(high[i] - low[i], 1e-9)
        upper_wick = high[i] - max(close[i], open_[i])
        lower_wick = min(close[i], open_[i]) - low[i]

        if not np.isnan(last_swing_high) and high[i] > last_swing_high and close[i] < last_swing_high:
            if upper_wick / candle_range >= wick_ratio:
                sweep_high[i] = 1

        if not np.isnan(last_swing_low) and low[i] < last_swing_low and close[i] > last_swing_low:
            if lower_wick / candle_range >= wick_ratio:
                sweep_low[i] = 1

    return pd.DataFrame({"liquidity_sweep_high": sweep_high, "liquidity_sweep_low": sweep_low}, index=df.index)
