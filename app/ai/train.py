"""
Model training — Primary Triple Barrier classifier + Secondary Meta-Labeler.

Split: 70% train / 15% val / 15% test (chronological order, zero shuffle).
Saves:
- models/xgb_model.pkl   (Primary direction classifier)
- models/meta_model.pkl  (Secondary trade profitability classifier)

Run:
    python -m app.ai.train
"""
import logging
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import classification_report
from sklearn.ensemble import HistGradientBoostingClassifier

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.ai.feature_engineering import (
    FEATURE_COLS, make_triple_barrier_labels, prepare_features, LABEL_MAP, INT_MAP
)
from app.ai.meta_labeler import train_meta_labeler
from app.monitoring.logger import setup_logging

logger = logging.getLogger(__name__)

MODEL_PATH = Path(os.getenv("MODEL_DIR", "models")) / "xgb_model.pkl"
TRAIN_FRAC = 0.70
VAL_FRAC   = 0.15


def train(df: pd.DataFrame) -> dict:
    """
    Train Primary Triple Barrier classifier and Secondary Meta-Labeler.
    """
    labels = make_triple_barrier_labels(df)
    features = prepare_features(df)

    # Valid mask removes rows where future barrier touch cannot be evaluated (end of dataset)
    valid_mask = labels.notna()
    X = features[valid_mask].fillna(0).astype(float)
    y = labels[valid_mask].astype(int)

    n = len(X)
    train_end = int(n * TRAIN_FRAC)
    val_end   = int(n * (TRAIN_FRAC + VAL_FRAC))

    X_train, y_train = X.iloc[:train_end], y.iloc[:train_end]
    X_val,   y_val   = X.iloc[train_end:val_end], y.iloc[train_end:val_end]
    X_test,  y_test  = X.iloc[val_end:], y.iloc[val_end:]

    logger.info("Training Primary Triple-Barrier Model (Train: %d, Val: %d, Test: %d)",
                len(X_train), len(X_val), len(X_test))

    # Calculate class weights for imbalance handling
    counts = y_train.value_counts()
    max_c = counts.max()
    scale_weights = {c: float(max_c / count) for c, count in counts.items()}

    model = None
    try:
        import xgboost as xgb
        model = xgb.XGBClassifier(
            n_estimators=150,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            objective="multi:softprob",
            num_class=3,
            eval_metric="mlogloss",
            early_stopping_rounds=15,
            random_state=42,
            n_jobs=-1,
        )
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False,
            sample_weight=[scale_weights.get(c, 1.0) for c in y_train],
        )
        logger.info("Primary model trained using XGBoost")
    except Exception as e:
        logger.warning("XGBoost initialization fallback: %s; using HistGradientBoostingClassifier", e)
        model = HistGradientBoostingClassifier(
            max_iter=150,
            max_depth=4,
            learning_rate=0.05,
            early_stopping=True,
            random_state=42,
        )
        model.fit(
            X_train, y_train,
            sample_weight=[scale_weights.get(c, 1.0) for c in y_train],
        )
        logger.info("Primary model trained using HistGradientBoostingClassifier")

    # Evaluate on test set
    y_pred = model.predict(X_test)
    report = classification_report(
        y_test, y_pred,
        target_names=["SELL", "HOLD", "BUY"],
        output_dict=True,
        zero_division=0,
    )
    logger.info("Primary Model Test Set Report:\n%s",
                classification_report(y_test, y_pred,
                                      target_names=["SELL", "HOLD", "BUY"],
                                      zero_division=0))

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    logger.info("Primary model saved to %s", MODEL_PATH)

    # ── Train Meta-Labeler ────────────────────────────────────────────────────
    y_pred_all = model.predict(X)
    future_returns = (df["close"].shift(-4) - df["close"]) / df["close"]
    actual_future_returns = future_returns[valid_mask].fillna(0).values

    logger.info("Training Secondary Meta-Labeler Precision Filter...")
    meta_results = train_meta_labeler(
        X=X,
        primary_predictions=y_pred_all,
        actual_future_returns=actual_future_returns,
    )

    return {
        "primary_model": model,
        "test_report": report,
        "meta_accuracy": meta_results.get("accuracy", 0.5),
        "feature_cols": FEATURE_COLS,
    }


if __name__ == "__main__":
    setup_logging()
    from dotenv import load_dotenv
    load_dotenv()

    from app.data.market_data import fetch_and_store
    from app.data.preprocessing import preprocess
    from app.data.indicators import add_indicators

    logger.info("Fetching data for training...")
    raw_df  = fetch_and_store()
    proc_df = preprocess(raw_df)
    feat_df = add_indicators(proc_df, shift=True).dropna()

    results = train(feat_df)
    logger.info("Training complete! Primary Test Accuracy: %.4f, Meta-Labeler Accuracy: %.4f",
                results["test_report"]["accuracy"], results["meta_accuracy"])
