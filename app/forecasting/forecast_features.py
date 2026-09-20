"""
Forecast-derived features for XGBoost input.

Takes a ForecastResult and current price, returns a flat dict of features.
"""
import numpy as np
from app.forecasting.chronos_model import ForecastResult


def extract_forecast_features(
    result: ForecastResult,
    current_price: float,
    horizon: int = 1,      # which step to use as primary forecast (0-indexed)
) -> dict:
    """
    Convert a Chronos ForecastResult into a feature dict for XGBoost.

    Features produced
    -----------------
    forecast_price      : median forecast at `horizon` steps
    forecast_return     : (forecast - current) / current
    forecast_direction  : +1 bullish, -1 bearish, 0 neutral (abs < 0.001)
    forecast_iqr        : IQR ratio (uncertainty)
    forecast_lo_return  : 10th-pct return (downside risk)
    forecast_hi_return  : 90th-pct return (upside potential)
    """
    fc_price = float(result.median[horizon])
    fc_ret   = (fc_price - current_price) / current_price if current_price > 0 else 0.0

    if fc_ret > 0.001:
        direction = 1
    elif fc_ret < -0.001:
        direction = -1
    else:
        direction = 0

    lo_ret = (float(result.low_q[horizon])  - current_price) / current_price
    hi_ret = (float(result.high_q[horizon]) - current_price) / current_price

    return {
        "forecast_price":    fc_price,
        "forecast_return":   fc_ret,
        "forecast_direction": direction,
        "forecast_iqr":      result.uncertainty,
        "forecast_lo_return": lo_ret,
        "forecast_hi_return": hi_ret,
    }
