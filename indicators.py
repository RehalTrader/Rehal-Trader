"""
Classic technical-indicator feature engineering.

All functions take a pandas DataFrame with columns: ['open','high','low','close','volume']
indexed by candle close time (ascending), and return either a pandas Series or add
column(s) to a copy of the DataFrame. Every function is pure / stateless so it can be
unit tested and reused identically in both training and live inference.
"""
import numpy as np
import pandas as pd


def rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    return (100 - (100 / (1 + rs))).fillna(50)


def qqe(df: pd.DataFrame, rsi_period: int = 14, smoothing: int = 5, factor: float = 4.236) -> pd.DataFrame:
    """
    Quantitative Qualitative Estimation — a smoothed-RSI trend-following oscillator
    with adaptive trailing bands. Returns columns: qqe_rsi_ma, qqe_fast_atr_rsi,
    qqe_trend (+1 bullish / -1 bearish).
    """
    rsi_series = rsi(df, rsi_period)
    rsi_ma = rsi_series.ewm(span=smoothing, adjust=False).mean()

    atr_rsi = rsi_ma.diff().abs().ewm(alpha=1 / rsi_period, adjust=False).mean()
    smoothed_atr_rsi = atr_rsi.ewm(alpha=1 / rsi_period, adjust=False).mean() * factor

    upper_band = rsi_ma + smoothed_atr_rsi
    lower_band = rsi_ma - smoothed_atr_rsi

    trend = pd.Series(index=df.index, dtype="float64")
    trailing_line = pd.Series(index=df.index, dtype="float64")
    trailing_line.iloc[0] = rsi_ma.iloc[0]
    trend.iloc[0] = 1

    for i in range(1, len(df)):
        prev_trailing = trailing_line.iloc[i - 1]
        if rsi_ma.iloc[i] > prev_trailing and rsi_ma.iloc[i - 1] > prev_trailing:
            trailing_line.iloc[i] = max(prev_trailing, lower_band.iloc[i])
        elif rsi_ma.iloc[i] < prev_trailing and rsi_ma.iloc[i - 1] < prev_trailing:
            trailing_line.iloc[i] = min(prev_trailing, upper_band.iloc[i])
        elif rsi_ma.iloc[i] > prev_trailing:
            trailing_line.iloc[i] = lower_band.iloc[i]
        else:
            trailing_line.iloc[i] = upper_band.iloc[i]

        trend.iloc[i] = 1 if rsi_ma.iloc[i] >= trailing_line.iloc[i] else -1

    return pd.DataFrame({"qqe_rsi_ma": rsi_ma, "qqe_trend": trend})


def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def ema_trend(df: pd.DataFrame, fast: int = 20, slow: int = 50, macro: int = 200) -> pd.DataFrame:
    """Multi-timeframe EMA stack. trend_score: +2 strong up, +1 up, 0 mixed, -1 down, -2 strong down."""
    ema_fast, ema_slow, ema_macro = ema(df["close"], fast), ema(df["close"], slow), ema(df["close"], macro)

    trend_score = pd.Series(0, index=df.index)
    trend_score += np.where(ema_fast > ema_slow, 1, -1)
    trend_score += np.where(ema_slow > ema_macro, 1, -1)

    return pd.DataFrame({"ema_fast": ema_fast, "ema_slow": ema_slow, "ema_macro": ema_macro, "trend_score": trend_score})


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [df["high"] - df["low"], (df["high"] - prev_close).abs(), (df["low"] - prev_close).abs()], axis=1
    ).max(axis=1)
    return tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()


def macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    macd_line = ema(df["close"], fast) - ema(df["close"], slow)
    signal_line = ema(macd_line, signal)
    return pd.DataFrame({"macd": macd_line, "macd_signal": signal_line, "macd_hist": macd_line - signal_line})


def bollinger_bands(df: pd.DataFrame, period: int = 20, std_mult: float = 2.0) -> pd.DataFrame:
    mid = df["close"].rolling(period).mean()
    std = df["close"].rolling(period).std()
    upper, lower = mid + std_mult * std, mid - std_mult * std
    percent_b = (df["close"] - lower) / (upper - lower).replace(0, np.nan)
    return pd.DataFrame({"bb_upper": upper, "bb_mid": mid, "bb_lower": lower, "bb_percent_b": percent_b.fillna(0.5)})


def volume_features(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
    vol_ma = df["volume"].rolling(period).mean()
    return pd.DataFrame(
        {
            "volume_ma": vol_ma,
            "volume_ratio": (df["volume"] / vol_ma.replace(0, np.nan)).fillna(1.0),
            "volume_zscore": ((df["volume"] - vol_ma) / df["volume"].rolling(period).std().replace(0, np.nan)).fillna(0),
        }
    )


def support_resistance(df: pd.DataFrame, lookback: int = 50, tolerance_pct: float = 0.001) -> pd.DataFrame:
    """
    Simple swing-based S/R: rolling max/min of highs/lows as dynamic resistance/support,
    plus a binary flag for whether price is currently "near" one of those levels.
    """
    resistance = df["high"].rolling(lookback).max()
    support = df["low"].rolling(lookback).min()

    near_resistance = (resistance - df["close"]).abs() / df["close"] < tolerance_pct
    near_support = (df["close"] - support).abs() / df["close"] < tolerance_pct

    return pd.DataFrame(
        {
            "resistance": resistance,
            "support": support,
            "near_resistance": near_resistance.astype(int),
            "near_support": near_support.astype(int),
        }
    )
