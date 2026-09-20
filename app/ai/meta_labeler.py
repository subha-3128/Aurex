"""
Meta-Labeler — predicts probability that a trade will be profitable after fees.
Thin wrapper: returns 0.60 confidence by default if model file not found.
"""
from __future__ import annotations
import logging
import os
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

_META_PATH = Path(os.getenv("MODEL_DIR", "models")) / "meta_labeler.pkl"
_meta_model = None


def _load_meta():
    global _meta_model
    if _meta_model is None:
        if _META_PATH.exists():
            import joblib
            _meta_model = joblib.load(_META_PATH)
        else:
            _meta_model = False  # sentinel: not available
    return _meta_model


def predict_meta_confidence(X: pd.DataFrame) -> float:
    """Return estimated probability that trade is profitable after fees (0-1)."""
    model = _load_meta()
    if model is False:
        return 0.60  # neutral default when model not trained yet
    try:
        proba = model.predict_proba(X)[0]
        return float(proba[1])  # probability of class 1 (profitable)
    except Exception as e:
        logger.debug("Meta-labeler inference error: %s", e)
        return 0.60
