"""
Market regime detector — deterministic rule-based classifier.

5 states: BULL | BEAR | SIDEWAYS | HIGH_VOL | LOW_VOL

Inputs:
  ema_50, ema_200, atr_pct, ret_24, roll_std_20, vol_regime

No ML model needed — deterministic rules are faster and auditable.
ponytail: ML regime model only if rules measurably fail.
"""
import logging
import pandas as pd

logger = logging.getLogger(__name__)

REGIMES = ("BULL", "BEAR", "SIDEWAYS", "HIGH_VOL", "LOW_VOL")


def detect_regime(row: pd.Series) -> str:
    """
    Classify a single candle's market regime.

    Parameters
    ----------
    row : Series with fields: close, ema_50, ema_200, atr_pct,
                               ret_24, roll_std_20, vol_regime

    Returns
    -------
    str — one of REGIMES
    """
    atr_pct   = float(row.get("atr_pct", 0) or 0)
    vol_regime = int(row.get("vol_regime", 0) or 0)
    close     = float(row.get("close", 0) or 0)
    ema_50    = float(row.get("ema_50", 0) or 0)
    ema_200   = float(row.get("ema_200", 0) or 0)
    ret_24    = float(row.get("ret_24", 0) or 0)

    # Priority 1: extreme volatility overrides trend
    if atr_pct > 0.03 or vol_regime == 1:
        return "HIGH_VOL"

    # Priority 2: very low volatility
    if atr_pct < 0.005 and vol_regime == 0:
        return "LOW_VOL"

    # Priority 3: trend (Golden/Death cross region)
    if ema_50 > 0 and ema_200 > 0:
        if close > ema_50 > ema_200 and ret_24 > 0.005:
            return "BULL"
        if close < ema_50 < ema_200 and ret_24 < -0.005:
            return "BEAR"

    return "SIDEWAYS"


def add_regime_column(df: pd.DataFrame) -> pd.DataFrame:
    """Apply regime detection to every row; returns new DataFrame."""
    df = df.copy()
    df["regime"] = df.apply(detect_regime, axis=1)
    return df


# Regime → risk multiplier (applied to position size in Risk Shield)
REGIME_RISK_MULTIPLIER: dict[str, float] = {
    "BULL":      1.0,
    "BEAR":      0.5,
    "SIDEWAYS":  0.75,
    "HIGH_VOL":  0.3,
    "LOW_VOL":   0.8,
}
