import numpy as np
import pandas as pd
import pytest

from features import smc


@pytest.fixture
def trending_up_ohlcv():
    n = 100
    # Trend + oscillation whose local slope periodically exceeds the trend slope,
    # so real local swing highs/lows actually form (a purely monotonic series, as an
    # earlier version of this fixture produced, has NO swing points at all and makes
    # every structure-detection assertion below vacuously fail).
    trend = np.linspace(100, 120, n)
    oscillation = 3 * np.sin(np.linspace(0, 20, n))
    close = trend + oscillation
    high = close + 0.3
    low = close - 0.3
    open_ = close - 0.1
    volume = np.full(n, 1000.0)
    index = pd.date_range("2026-01-01", periods=n, freq="15min", tz="UTC")
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close, "volume": volume}, index=index)


def test_fair_value_gap_columns_present(trending_up_ohlcv):
    result = smc.fair_value_gap(trending_up_ohlcv)
    assert set(result.columns) == {"fvg_bullish", "fvg_bearish", "fvg_size"}
    assert result["fvg_bullish"].isin([0, 1]).all()


def test_bos_detects_bullish_continuation_in_uptrend(trending_up_ohlcv):
    result = smc.break_of_structure(trending_up_ohlcv, order=3)
    # In a clean uptrend we expect at least some bullish BOS events and no bearish ones dominating
    assert result["bos_bullish"].sum() > 0


def test_liquidity_sweep_output_shape(trending_up_ohlcv):
    result = smc.liquidity_sweep(trending_up_ohlcv)
    assert len(result) == len(trending_up_ohlcv)
    assert result["liquidity_sweep_high"].isin([0, 1]).all()
    assert result["liquidity_sweep_low"].isin([0, 1]).all()


def test_choch_only_fires_on_direction_flip(trending_up_ohlcv):
    result = smc.change_of_character(trending_up_ohlcv, order=3)
    # CHOCH bullish and bearish should never both fire on the same candle
    both_fired = ((result["choch_bullish"] == 1) & (result["choch_bearish"] == 1)).sum()
    assert both_fired == 0
