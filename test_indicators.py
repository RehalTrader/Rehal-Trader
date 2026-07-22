import numpy as np
import pandas as pd
import pytest

from features import indicators


@pytest.fixture
def sample_ohlcv():
    rng = np.random.default_rng(42)
    n = 300
    close = 100 + np.cumsum(rng.normal(0, 0.5, n))
    high = close + rng.uniform(0, 0.5, n)
    low = close - rng.uniform(0, 0.5, n)
    open_ = close + rng.normal(0, 0.2, n)
    volume = rng.uniform(1000, 5000, n)
    index = pd.date_range("2026-01-01", periods=n, freq="15min", tz="UTC")
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close, "volume": volume}, index=index)


def test_rsi_bounded_between_0_and_100(sample_ohlcv):
    result = indicators.rsi(sample_ohlcv)
    assert result.min() >= 0
    assert result.max() <= 100


def test_atr_is_non_negative(sample_ohlcv):
    result = indicators.atr(sample_ohlcv)
    assert (result.dropna() >= 0).all()


def test_macd_returns_expected_columns(sample_ohlcv):
    result = indicators.macd(sample_ohlcv)
    assert set(result.columns) == {"macd", "macd_signal", "macd_hist"}
    assert len(result) == len(sample_ohlcv)


def test_bollinger_percent_b_reasonable_range(sample_ohlcv):
    result = indicators.bollinger_bands(sample_ohlcv)
    valid = result["bb_percent_b"].dropna()
    # percent_b can occasionally exceed [0,1] on breakouts, but shouldn't be wildly off
    assert valid.between(-1, 2).all()


def test_ema_trend_score_range(sample_ohlcv):
    result = indicators.ema_trend(sample_ohlcv)
    assert result["trend_score"].isin([-2, 0, 2]).all() or result["trend_score"].between(-2, 2).all()
