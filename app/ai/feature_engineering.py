"""
Feature engineering & Triple Barrier Labeling.

Combines:
1. Technical indicators (pure pandas)
2. Multi-timeframe macro indicators (4h EMA/RSI)
3. Derivatives microstructure (Funding Rate, Open Interest)
4. Chronos forecast features

Labeling:
López de Prado Triple Barrier Method:
- Upper Barrier: Take Profit (+1.5 x ATR)
- Lower Barrier: Stop Loss (-1.5 x ATR)
- Vertical Barrier: Max holding period (6 bars)
"""
import logging
import os

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

LABEL_THRESHOLD  = float(os.getenv("LABEL_THRESHOLD",  "0.003"))   # 0.3%
FORECAST_HORIZON = int(os.getenv("FORECAST_HORIZON",   "4"))
TAKER_FEE        = float(os.getenv("TAKER_FEE",        "0.001"))

# Cost-adjusted threshold: must exceed round-trip fees
COST_ADJ_THRESHOLD = LABEL_THRESHOLD + 2 * TAKER_FEE

LABEL_MAP = {0: "SELL", 1: "HOLD", 2: "BUY"}
INT_MAP   = {"SELL": 0, "HOLD": 1, "BUY": 2}

# Ordered list of feature columns used by the models
FEATURE_COLS = [
    # Core technicals
    "rsi_14", "ema_diff_9_21", "ema_diff_21_50", "macd_hist", "macd",
    "atr_pct", "roll_std_20", "vol_regime",
    "rel_volume", "volume_change",
    "recent_drawdown", "consec_gains", "consec_losses", "trend_dir",
    "ret_1", "log_ret_1", "ret_4", "ret_24",
    # Multi-timeframe macro confluence
    "macro_rsi", "macro_trend",
    # Derivatives microstructure
    "funding_rate", "open_interest_delta",
    # Chronos features
    "forecast_return", "forecast_direction", "forecast_iqr",
    "forecast_lo_return", "forecast_hi_return",
]


def make_triple_barrier_labels(
    df: pd.DataFrame,
    pt_mult: float = 1.5,
    sl_mult: float = 1.5,
    max_bars: int = 6,
) -> pd.Series:
    """
    Generate Triple Barrier labels (López de Prado formulation).
    
    For each bar:
    - Upper Barrier: entry * (1 + max(COST_ADJ_THRESHOLD, pt_mult * atr_pct))
    - Lower Barrier: entry * (1 - max(COST_ADJ_THRESHOLD, sl_mult * atr_pct))
    - Vertical Barrier: max_bars ahead
    
    Returns
    -------
    pd.Series with integer labels: 2=BUY, 0=SELL, 1=HOLD, and NaN for the final max_bars rows.
    """
    n = len(df)
    labels = pd.Series(1, index=df.index, dtype=float, name="label")  # Default HOLD
    
    close = df["close"].values
    high = df["high"].values
    low = df["low"].values
    atr_pct = df["atr_pct"].values if "atr_pct" in df.columns else np.full(n, 0.015)
    
    for i in range(n - max_bars):
        entry_p = close[i]
        curr_atr = atr_pct[i] if not np.isnan(atr_pct[i]) else 0.015
        
        pt_dist = max(COST_ADJ_THRESHOLD, pt_mult * curr_atr)
        sl_dist = max(COST_ADJ_THRESHOLD, sl_mult * curr_atr)
        
        upper_barrier = entry_p * (1.0 + pt_dist)
        lower_barrier = entry_p * (1.0 - sl_dist)
        
        label = 1  # default HOLD if timeout
        for j in range(1, max_bars + 1):
            bar_high = high[i + j]
            bar_low = low[i + j]
            
            touch_upper = bar_high >= upper_barrier
            touch_lower = bar_low <= lower_barrier
            
            if touch_upper and not touch_lower:
                label = 2  # BUY was correct
                break
            elif touch_lower and not touch_upper:
                label = 0  # SELL was correct
                break
            elif touch_upper and touch_lower:
                # Both touched in same bar: choose based on candle close
                label = 2 if close[i + j] >= entry_p else 0
                break
                
        labels.iloc[i] = label

    # Final max_bars cannot be labeled
    labels.iloc[-max_bars:] = np.nan
    return labels


def make_labels(df: pd.DataFrame) -> pd.Series:
    """Primary labeling function using Triple Barrier method."""
    return make_triple_barrier_labels(df)


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract the model feature matrix from a processed DataFrame.
    Fills missing features with neutral fallback defaults.
    """
    feat_df = pd.DataFrame(index=df.index)
    for col in FEATURE_COLS:
        if col in df.columns:
            feat_df[col] = df[col]
        else:
            # Neutral fallbacks
            if col == "macro_rsi":
                feat_df[col] = 50.0
            elif col == "funding_rate":
                feat_df[col] = 0.0001
            else:
                feat_df[col] = 0.0
    return feat_df


def get_feature_row(row: pd.Series) -> pd.DataFrame:
    """Extract a single-row feature DataFrame for live inference."""
    feat = {}
    for col in FEATURE_COLS:
        val = row.get(col)
        if val is None or pd.isna(val):
            if col == "macro_rsi":
                val = 50.0
            elif col == "funding_rate":
                val = 0.0001
            else:
                val = 0.0
        feat[col] = float(val)
    return pd.DataFrame([feat], columns=FEATURE_COLS)
