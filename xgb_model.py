"""
XGBoost classifier: predicts P(price up) over the next `horizon` candles from the
engineered feature snapshot at the current closed candle. Good at capturing nonlinear
interactions between discrete structural features (BOS/CHOCH/FVG/session flags).
"""
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split

from features.pipeline import FEATURE_COLUMNS

logger = logging.getLogger(__name__)

DEFAULT_MODEL_PATH = Path(__file__).parent / "artifacts" / "xgb_model.json"


class XGBSignalModel:
    def __init__(self, model_path: Path = DEFAULT_MODEL_PATH):
        self.model_path = model_path
        self.model: xgb.XGBClassifier | None = None
        if model_path.exists():
            self.load()

    def train(self, features: pd.DataFrame, labels: pd.Series, test_size: float = 0.2) -> dict:
        """labels: 1 if price moved up by more than threshold over the horizon, else 0."""
        X_train, X_test, y_train, y_test = train_test_split(
            features[FEATURE_COLUMNS], labels, test_size=test_size, shuffle=False  # no shuffle: time series
        )

        self.model = xgb.XGBClassifier(
            n_estimators=400,
            max_depth=5,
            learning_rate=0.03,
            subsample=0.8,
            colsample_bytree=0.8,
            eval_metric="logloss",
            n_jobs=-1,
        )
        self.model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

        train_acc = self.model.score(X_train, y_train)
        test_acc = self.model.score(X_test, y_test)
        logger.info("XGB trained — train_acc=%.3f test_acc=%.3f", train_acc, test_acc)
        return {"train_accuracy": train_acc, "test_accuracy": test_acc}

    def predict_proba_up(self, feature_row: pd.DataFrame) -> float:
        if self.model is None:
            raise RuntimeError("XGB model not trained/loaded yet.")
        proba = self.model.predict_proba(feature_row[FEATURE_COLUMNS])[:, 1]
        return float(proba[-1])

    def save(self) -> None:
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, self.model_path)

    def load(self) -> None:
        self.model = joblib.load(self.model_path)


def make_labels(df: pd.DataFrame, horizon: int = 3, threshold_pct: float = 0.0005) -> pd.Series:
    """Binary label: 1 if close[t+horizon] is up more than threshold_pct vs close[t]."""
    future_return = df["close"].shift(-horizon) / df["close"] - 1
    return (future_return > threshold_pct).astype(int).iloc[:-horizon]
