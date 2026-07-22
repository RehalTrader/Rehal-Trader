"""
LSTM: captures temporal/sequential patterns (momentum build-up, trend persistence)
across a rolling window of candles that a single-row XGBoost snapshot can't see.
Outputs the same P(up) probability as XGB so the two can be ensembled directly.
"""
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.preprocessing import StandardScaler

from features.pipeline import FEATURE_COLUMNS

logger = logging.getLogger(__name__)

DEFAULT_MODEL_DIR = Path(__file__).parent / "artifacts" / "lstm_model"
SEQUENCE_LENGTH = 30  # candles of lookback per training/inference sample


def _build_sequences(features: pd.DataFrame, labels: pd.Series | None, seq_len: int):
    values = features[FEATURE_COLUMNS].values
    X, y = [], []
    for i in range(seq_len, len(values)):
        X.append(values[i - seq_len : i])
        if labels is not None:
            y.append(labels.iloc[i])
    X = np.array(X)
    y = np.array(y) if labels is not None else None
    return X, y


class LSTMSignalModel:
    def __init__(self, model_dir: Path = DEFAULT_MODEL_DIR, sequence_length: int = SEQUENCE_LENGTH):
        self.model_dir = model_dir
        self.sequence_length = sequence_length
        self.model: tf.keras.Model | None = None
        self.scaler = StandardScaler()
        if model_dir.exists():
            self.load()

    def _build_model(self, n_features: int) -> tf.keras.Model:
        model = tf.keras.Sequential(
            [
                tf.keras.layers.Input(shape=(self.sequence_length, n_features)),
                tf.keras.layers.LSTM(64, return_sequences=True),
                tf.keras.layers.Dropout(0.2),
                tf.keras.layers.LSTM(32),
                tf.keras.layers.Dropout(0.2),
                tf.keras.layers.Dense(16, activation="relu"),
                tf.keras.layers.Dense(1, activation="sigmoid"),
            ]
        )
        model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
        return model

    def train(self, features: pd.DataFrame, labels: pd.Series, epochs: int = 20, batch_size: int = 64) -> dict:
        self.scaler.fit(features[FEATURE_COLUMNS])
        scaled = features.copy()
        scaled[FEATURE_COLUMNS] = self.scaler.transform(features[FEATURE_COLUMNS])

        X, y = _build_sequences(scaled, labels, self.sequence_length)
        split = int(len(X) * 0.8)
        X_train, X_test, y_train, y_test = X[:split], X[split:], y[:split], y[split:]

        self.model = self._build_model(n_features=len(FEATURE_COLUMNS))
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_test, y_test),
            epochs=epochs, batch_size=batch_size, verbose=0,
        )
        test_acc = history.history["val_accuracy"][-1]
        logger.info("LSTM trained — final val_accuracy=%.3f", test_acc)
        return {"val_accuracy": test_acc}

    def predict_proba_up(self, feature_window: pd.DataFrame) -> float:
        """feature_window must contain the last `sequence_length` rows of features."""
        if self.model is None:
            raise RuntimeError("LSTM model not trained/loaded yet.")
        scaled = self.scaler.transform(feature_window[FEATURE_COLUMNS].tail(self.sequence_length))
        X = np.expand_dims(scaled, axis=0)
        return float(self.model.predict(X, verbose=0)[0][0])

    def save(self) -> None:
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.model.save(self.model_dir / "model.keras")
        import joblib
        joblib.dump(self.scaler, self.model_dir / "scaler.pkl")

    def load(self) -> None:
        import joblib
        self.model = tf.keras.models.load_model(self.model_dir / "model.keras")
        self.scaler = joblib.load(self.model_dir / "scaler.pkl")
