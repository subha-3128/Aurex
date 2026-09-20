"""
Technical strategy — Experiment A baseline (rule-based, no ML).

Rules
-----
BUY  : RSI < 40  AND EMA9 > EMA21 AND MACD hist > 0 AND price > EMA50
SELL : RSI > 65  AND EMA9 < EMA21 AND MACD hist < 0 AND price < EMA50
HOLD : everything else

These thresholds are a research baseline, not optimal parameters.
"""
import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

Signal = str  # "BUY" | "SELL" | "HOLD"


def generate_signals(df: pd.DataFrame) -> pd.Series:
    """
    Apply rule-based strategy to a DataFrame with indicator columns.

    Returns a Series of signals ("BUY" / "SELL" / "HOLD") indexed
    identically to df.

    Expects columns: rsi_14, ema_9, ema_21, ema_50, macd_hist, close
    """
    required = ["rsi_14", "ema_9", "ema_21", "ema_50", "macd_hist", "close"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing indicator columns: {missing}")

    signals = pd.Series("HOLD", index=df.index, dtype=str)

    buy_mask = (
        (df["rsi_14"] < 40) &
        (df["ema_9"]  > df["ema_21"]) &
        (df["macd_hist"] > 0) &
        (df["close"]  > df["ema_50"])
    )

    sell_mask = (
        (df["rsi_14"] > 65) &
        (df["ema_9"]  < df["ema_21"]) &
        (df["macd_hist"] < 0) &
        (df["close"]  < df["ema_50"])
    )

    signals[buy_mask]  = "BUY"
    signals[sell_mask] = "SELL"

    logger.debug(
        "Signals: BUY=%d SELL=%d HOLD=%d",
        buy_mask.sum(), sell_mask.sum(), (~buy_mask & ~sell_mask).sum(),
    )
    return signals


def generate_signal_row(row: pd.Series) -> Signal:
    """Generate a signal for a single row (live use)."""
    single = row.to_frame().T
    return generate_signals(single).iloc[0]
