"""
Technical indicators — implemented in pure pandas/numpy.

No external TA library required.  All indicators are standard formulas.
All indicator columns are shifted by 1 (default) to prevent look-ahead
bias when used as training features.

Usage
-----
from app.data.indicators import add_indicators
df = add_indicators(df)    # returns new df with indicator columns
"""
import logging
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ── Private helpers ───────────────────────────────────────────────────────────

def _ema(series: pd.Series, span: int) -> pd.Series:
    """Exponential moving average (pandas ewm, min_periods=span)."""
    return series.ewm(span=span, min_periods=span, adjust=False).mean()


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Wilder's RSI."""
    delta = close.diff()
    gain  = delta.clip(lower=0)
    loss  = (-delta).clip(lower=0)
    # Use Wilder smoothing (equivalent to ewm alpha=1/period)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, float("nan"))
    return 100 - (100 / (1 + rs))


def _macd(
    close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Returns (macd_line, signal_line, histogram)."""
    ema_fast    = _ema(close, fast)
    ema_slow    = _ema(close, slow)
    macd_line   = ema_fast - ema_slow
    signal_line = _ema(macd_line, signal)
    histogram   = macd_line - signal_line
    return macd_line, signal_line, histogram


def _atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Average True Range (Wilder smoothing)."""
    prev_close = close.shift(1)
    tr = pd.concat(
        [high - low,
         (high - prev_close).abs(),
         (low  - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()


def _consecutive_direction(series: pd.Series, positive: bool) -> pd.Series:
    """Count consecutive positive (or negative) values ending at each row."""
    sign  = (series > 0) if positive else (series < 0)
    block = (sign != sign.shift()).cumsum()
    return sign.groupby(block).cumsum().astype(int)


# ── Public API ────────────────────────────────────────────────────────────────

def add_indicators(df: pd.DataFrame, shift: bool = True) -> pd.DataFrame:
    """
    Compute and attach technical indicators to the DataFrame.

    Parameters
    ----------
    df    : OHLCV DataFrame with columns [open, high, low, close, volume]
    shift : If True (default), shift all indicator columns by 1 to prevent
            look-ahead bias during model training.

    Returns
    -------
    DataFrame with indicator columns appended. Rows with leading NaN
    (due to warm-up periods) are NOT dropped here — caller decides.
    """
    df = df.copy()
    close  = df["close"]
    high   = df["high"]
    low    = df["low"]
    volume = df["volume"]

    # ── Trend ────────────────────────────────────────────────────────────────
    df["ema_9"]   = _ema(close, 9)
    df["ema_21"]  = _ema(close, 21)
    df["ema_50"]  = _ema(close, 50)
    df["ema_200"] = _ema(close, 200)
    df["sma_20"]  = close.rolling(20).mean()

    df["ema_diff_9_21"]  = df["ema_9"]  - df["ema_21"]
    df["ema_diff_21_50"] = df["ema_21"] - df["ema_50"]

    # ── Momentum ─────────────────────────────────────────────────────────────
    df["rsi_14"] = _rsi(close, 14)

    macd_line, signal_line, hist = _macd(close, 12, 26, 9)
    df["macd"]        = macd_line
    df["macd_signal"] = signal_line
    df["macd_hist"]   = hist

    # ── Volatility ───────────────────────────────────────────────────────────
    df["atr_14"]      = _atr(high, low, close, 14)
    df["roll_std_20"] = close.pct_change().rolling(20).std()
    df["atr_pct"]     = df["atr_14"] / close

    roll_std_pctl = df["roll_std_20"].rolling(200, min_periods=50).quantile(0.70)
    df["vol_regime"] = (df["roll_std_20"] > roll_std_pctl).astype(int)

    # ── Volume ───────────────────────────────────────────────────────────────
    df["volume_ma_20"]  = volume.rolling(20).mean()
    df["rel_volume"]    = volume / df["volume_ma_20"].replace(0, float("nan"))
    df["volume_change"] = volume.pct_change()

    # ── Market state ─────────────────────────────────────────────────────────
    rolling_max = close.rolling(24, min_periods=1).max()
    df["recent_drawdown"] = (close - rolling_max) / rolling_max

    rets = close.pct_change()
    df["consec_gains"]  = _consecutive_direction(rets,  positive=True)
    df["consec_losses"] = _consecutive_direction(rets, positive=False)

    df["trend_dir"] = (close > df["ema_50"]).map({True: 1, False: -1})

    # ── Multi-Timeframe 4h Macro Confluence ──────────────────────────────────
    try:
        if len(df) >= 40 and isinstance(df.index, pd.DatetimeIndex):
            df_4h = df[["open", "high", "low", "close", "volume"]].resample("4h").agg({
                "open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"
            }).dropna()
            
            if len(df_4h) >= 15:
                ema50_4h = _ema(df_4h["close"], 50)
                rsi_4h   = _rsi(df_4h["close"], 14)
                # Shift 4h metrics by 1 completed 4h candle to prevent look-ahead bias
                macro_df = pd.DataFrame({
                    "macro_ema_50": ema50_4h.shift(1),
                    "macro_rsi":    rsi_4h.shift(1),
                }, index=df_4h.index)
                
                # Re-align forward onto 1h bars
                macro_aligned = macro_df.reindex(df.index, method="ffill")
                df["macro_ema_50"] = macro_aligned["macro_ema_50"].fillna(df["ema_50"])
                df["macro_rsi"]    = macro_aligned["macro_rsi"].fillna(50.0)
                df["macro_trend"]  = (close > df["macro_ema_50"]).map({True: 1, False: -1}).fillna(0)
            else:
                df["macro_ema_50"] = df["ema_50"]
                df["macro_rsi"]    = 50.0
                df["macro_trend"]  = 0
        else:
            df["macro_ema_50"] = df["ema_50"]
            df["macro_rsi"]    = 50.0
            df["macro_trend"]  = 0
    except Exception as e:
        logger.debug("Macro 4h calculation fallback: %s", e)
        df["macro_ema_50"] = df["ema_50"]
        df["macro_rsi"]    = 50.0
        df["macro_trend"]  = 0

    # ── Shift to prevent look-ahead bias ─────────────────────────────────────
    raw_cols = {"open", "high", "low", "close", "volume",
                "ret_1", "log_ret_1", "ret_4", "ret_24"}
    indicator_cols = [c for c in df.columns if c not in raw_cols]
    if shift:
        df[indicator_cols] = df[indicator_cols].shift(1)
        logger.debug(
            "Shifted %d indicator columns by 1 to prevent look-ahead bias",
            len(indicator_cols),
        )

    return df
