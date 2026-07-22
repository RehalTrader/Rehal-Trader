"""
Market session features, computed from the candle's UTC timestamp. Session timing
matters a lot for forex/gold volatility and liquidity, so we one-hot encode the
active session(s) and flag the high-liquidity London/NY overlap.
"""
import pandas as pd

SESSION_HOURS_UTC = {
    "sydney": (21, 6),   # wraps midnight
    "tokyo": (0, 9),
    "london": (7, 16),
    "new_york": (12, 21),
}


def _in_session(hour: int, start: int, end: int) -> bool:
    if start < end:
        return start <= hour < end
    return hour >= start or hour < end  # wraps past midnight


def market_sessions(df: pd.DataFrame) -> pd.DataFrame:
    """df.index must be timezone-aware (or naive-UTC) datetimes."""
    hours = df.index.hour if hasattr(df.index, "hour") else pd.to_datetime(df.index).hour

    out = {}
    for name, (start, end) in SESSION_HOURS_UTC.items():
        out[f"session_{name}"] = [int(_in_session(h, start, end)) for h in hours]

    out["session_london_ny_overlap"] = [
        int(_in_session(h, *SESSION_HOURS_UTC["london"]) and _in_session(h, *SESSION_HOURS_UTC["new_york"]))
        for h in hours
    ]

    return pd.DataFrame(out, index=df.index)
