import pandas as pd
import pytest

from models.ensemble import EnsembleWeights, SignalEnsemble


class _MockModel:
    """Returns a fixed probability regardless of input — isolates ensemble math from ML training."""

    def __init__(self, proba: float):
        self.proba = proba

    def predict_proba_up(self, _row_or_window) -> float:
        return self.proba


@pytest.mark.parametrize(
    "xgb_p,lstm_p,expected_direction",
    [
        (0.9, 0.9, "STRONG_BUY"),
        (0.6, 0.6, "BUY"),
        (0.5, 0.5, "NEUTRAL"),
        (0.4, 0.4, "SELL"),
        (0.1, 0.1, "STRONG_SELL"),
    ],
)
def test_ensemble_direction_classification(xgb_p, lstm_p, expected_direction):
    ensemble = SignalEnsemble(_MockModel(xgb_p), _MockModel(lstm_p), EnsembleWeights(0.5, 0.5))
    direction, confidence = ensemble.score(pd.DataFrame(), pd.DataFrame())
    assert direction == expected_direction
    assert 0 <= confidence <= 100


def test_ensemble_confidence_is_zero_at_indecision():
    ensemble = SignalEnsemble(_MockModel(0.5), _MockModel(0.5))
    _, confidence = ensemble.score(pd.DataFrame(), pd.DataFrame())
    assert confidence == 0


def test_ensemble_confidence_is_maximal_at_extremes():
    ensemble = SignalEnsemble(_MockModel(1.0), _MockModel(1.0))
    _, confidence = ensemble.score(pd.DataFrame(), pd.DataFrame())
    assert confidence == 100


def test_ensemble_respects_custom_weights():
    # XGB says strongly up, LSTM says strongly down, weighted 90/10 toward XGB -> still net up
    ensemble = SignalEnsemble(_MockModel(0.9), _MockModel(0.1), EnsembleWeights(0.9, 0.1))
    direction, _ = ensemble.score(pd.DataFrame(), pd.DataFrame())
    assert direction in ("BUY", "STRONG_BUY")
