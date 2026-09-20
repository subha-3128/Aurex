"""
XGBoost & Meta-Labeler inference — predict BUY/SELL/HOLD with precision filtering.
"""
import logging
import os
from pathlib import Path
from typing import TypedDict

import numpy as np
import pandas as pd
import joblib

from app.ai.feature_engineering import FEATURE_COLS, get_feature_row, LABEL_MAP
from app.ai.meta_labeler import predict_meta_confidence

logger = logging.getLogger(__name__)

MODEL_PATH = Path(os.getenv("MODEL_DIR", "models")) / "xgb_model.pkl"

# Singleton model cache
_model = None


def _load_model():
    global _model
    if _model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model not found at {MODEL_PATH}. Run: python -m app.ai.train"
            )
        _model = joblib.load(MODEL_PATH)
        logger.info("Decision model loaded from %s", MODEL_PATH)
    return _model


class PredictionResult(TypedDict):
    signal:          str      # "BUY" | "SELL" | "HOLD"
    buy_prob:        float
    sell_prob:       float
    hold_prob:       float
    confidence:      float    # primary model confidence
    meta_confidence: float    # secondary trade success probability
    meta_filtered:   bool     # True if meta-model pruned a trade to HOLD


def predict(row: pd.Series) -> PredictionResult:
    """
    Predict signal for a single feature row with Meta-Labeler confirmation.
    """
    model = _load_model()
    X = get_feature_row(row).fillna(0).astype(float)
    probs = model.predict_proba(X)[0]   # [sell_prob, hold_prob, buy_prob]

    sell_prob, hold_prob, buy_prob = float(probs[0]), float(probs[1]), float(probs[2])
    signal_idx = int(np.argmax(probs))
    raw_signal = LABEL_MAP[signal_idx]
    confidence = float(probs[signal_idx])

    # Secondary Meta-Labeler evaluation
    meta_conf = predict_meta_confidence(X)
    meta_filtered = False

    # If primary model wants to trade, but meta-model says low probability of profit after costs
    if raw_signal in ("BUY", "SELL") and meta_conf < 0.45:
        logger.info("Meta-labeler pruned %s signal (Meta confidence: %.2f < 0.45)", raw_signal, meta_conf)
        final_signal = "HOLD"
        meta_filtered = True
    else:
        final_signal = raw_signal

    return PredictionResult(
        signal=final_signal,
        buy_prob=buy_prob,
        sell_prob=sell_prob,
        hold_prob=hold_prob,
        confidence=confidence,
        meta_confidence=round(meta_conf, 3),
        meta_filtered=meta_filtered,
    )


# predict_batch removed — no backtesting in this system
