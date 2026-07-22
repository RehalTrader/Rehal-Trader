"""
Combines XGBoost's snapshot-based probability with the LSTM's sequence-based
probability into a single confidence score (0-100) and a 5-class direction label.
"""
from dataclasses import dataclass

from models.lstm_model import LSTMSignalModel
from models.xgb_model import XGBSignalModel


@dataclass
class EnsembleWeights:
    xgb_weight: float = 0.5
    lstm_weight: float = 0.5


class SignalEnsemble:
    def __init__(self, xgb_model: XGBSignalModel, lstm_model: LSTMSignalModel, weights: EnsembleWeights | None = None):
        self.xgb_model = xgb_model
        self.lstm_model = lstm_model
        self.weights = weights or EnsembleWeights()

    def score(self, snapshot_row, sequence_window) -> tuple[str, float]:
        """
        snapshot_row: single-row DataFrame of the latest closed candle's features (for XGB).
        sequence_window: DataFrame of the last N candles' features (for LSTM).
        Returns (direction_label, confidence_0_to_100).
        """
        p_up_xgb = self.xgb_model.predict_proba_up(snapshot_row)
        p_up_lstm = self.lstm_model.predict_proba_up(sequence_window)

        combined_p_up = self.weights.xgb_weight * p_up_xgb + self.weights.lstm_weight * p_up_lstm

        # Map combined probability -> 5-class direction + confidence.
        # Confidence is "distance from indecision (0.5)" rescaled to 0-100, so 0.5 -> 0%
        # and 0.0 or 1.0 -> 100%, matching how strongly the models agree on a direction.
        confidence = abs(combined_p_up - 0.5) * 200  # 0-100

        if combined_p_up >= 0.75:
            direction = "STRONG_BUY"
        elif combined_p_up >= 0.55:
            direction = "BUY"
        elif combined_p_up > 0.45:
            direction = "NEUTRAL"
        elif combined_p_up > 0.25:
            direction = "SELL"
        else:
            direction = "STRONG_SELL"

        return direction, round(confidence, 2)
