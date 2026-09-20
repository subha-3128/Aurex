"""
Data preprocessing — cleaning, validation, and return calculation.

Rules enforced
--------------
- Sorted by timestamp ascending
- No duplicate timestamps
- No missing candles (gaps flagged, not filled)
- OHLCV values must be positive
- No look-ahead bias: returns computed with shift(1)
"""
import logging
from typing import Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Expected column set
_OHLCV = ["open", "high", "low", "close", "volume"]

# Timeframe → expected gap between candles (milliseconds)
_TF_MS = {
    "1m": 60_000, "5m": 300_000, "15m": 900_000, "30m": 1_800_000,
    "1h": 3_600_000, "4h": 14_400_000, "1d": 86_400_000,
}


def validate_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and validate a raw OHLCV DataFrame.

    Returns a clean DataFrame. Logs warnings for any issues found.
    Raises ValueError if data is too broken to continue.
    """
    if df.empty:
        raise ValueError("Empty DataFrame — no data to process")

    # Ensure required columns exist
    missing = [c for c in _OHLCV if c not in df.columns]
    if missing:
        raise ValueError(f"Missing OHLCV columns: {missing}")

    original_len = len(df)

    # Sort by index (timestamp)
    df = df.sort_index()

    # Drop duplicate timestamps
    dupes = df.index.duplicated()
    if dupes.any():
        logger.warning("Dropping %d duplicate timestamps", dupes.sum())
        df = df[~dupes]

    # Drop rows with any NaN in OHLCV
    nan_mask = df[_OHLCV].isna().any(axis=1)
    if nan_mask.any():
        logger.warning("Dropping %d rows with NaN OHLCV values", nan_mask.sum())
        df = df[~nan_mask]

    # Drop rows with non-positive prices or volume
    invalid = (df[["open", "high", "low", "close"]] <= 0).any(axis=1) | (df["volume"] < 0)
    if invalid.any():
        logger.warning("Dropping %d rows with invalid (≤0) OHLCV values", invalid.sum())
        df = df[~invalid]

    # Sanity: high >= low, high >= open/close, low <= open/close
    hl_ok = (df["high"] >= df["low"]) & (df["high"] >= df["open"]) & \
            (df["high"] >= df["close"]) & (df["low"] <= df["open"]) & \
            (df["low"] <= df["close"])
    if (~hl_ok).any():
        logger.warning("Dropping %d rows with OHLC consistency errors", (~hl_ok).sum())
        df = df[hl_ok]

    cleaned_len = len(df)
    if cleaned_len < original_len:
        logger.info("Cleaned %d → %d rows (%d dropped)",
                    original_len, cleaned_len, original_len - cleaned_len)

    if len(df) < 50:
        raise ValueError(f"Too few rows after cleaning: {len(df)}")

    return df


def detect_gaps(df: pd.DataFrame, timeframe: str = "1h") -> list[Tuple]:
    """
    Return list of (start, end, n_missing) tuples for candle gaps.
    Does not fill gaps — caller decides how to handle them.
    """
    expected_gap_ms = _TF_MS.get(timeframe, 3_600_000)
    # Convert DatetimeIndex to milliseconds
    ts_ms = df.index.astype(np.int64) // 1_000_000
    diffs = np.diff(ts_ms)
    gaps = []
    for i, diff in enumerate(diffs):
        if diff > expected_gap_ms * 1.5:
            n_missing = int(diff / expected_gap_ms) - 1
            gaps.append((df.index[i], df.index[i + 1], n_missing))
    if gaps:
        logger.warning("Found %d candle gaps in data", len(gaps))
    return gaps


def add_returns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add return columns — all use shift(1) so there is zero look-ahead bias.

    Columns added
    -------------
    ret_1       : simple 1-period return
    log_ret_1   : log return
    ret_4       : 4-period rolling return
    ret_24      : 24-period rolling return
    """
    close = df["close"]
    df = df.copy()
    df["ret_1"]     = close.pct_change()                          # shift inside pct_change
    df["log_ret_1"] = np.log(close / close.shift(1))
    df["ret_4"]     = close.pct_change(4)
    df["ret_24"]    = close.pct_change(24)
    return df


def preprocess(df: pd.DataFrame, timeframe: str = "1h") -> pd.DataFrame:
    """
    Full preprocessing pipeline.

    1. validate_ohlcv
    2. detect_gaps (logs only)
    3. add_returns
    4. Drop the first row (NaN from shift)
    """
    df = validate_ohlcv(df)
    detect_gaps(df, timeframe)
    df = add_returns(df)
    df = df.dropna(subset=["ret_1"])   # first row always NaN
    return df
