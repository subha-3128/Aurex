"""
Chronos-2 forecasting layer.

Loads amazon/chronos-t5-small (or configured variant) and generates
probabilistic forecasts for the BTC/USDT close price series.

Singleton pattern — model loaded once per process.

If chronos-forecasting is not installed, raises ImportError with
install instructions.
"""
import logging
import os
from functools import lru_cache
from typing import NamedTuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

CHRONOS_MODEL    = os.getenv("CHRONOS_MODEL",    "amazon/chronos-t5-small")
CONTEXT_LEN      = int(os.getenv("CHRONOS_CONTEXT_LEN", "64"))
FORECAST_HORIZON = int(os.getenv("FORECAST_HORIZON",    "4"))


class ForecastResult(NamedTuple):
    median:      np.ndarray    # shape (horizon,)
    low_q:       np.ndarray    # 10th percentile
    high_q:      np.ndarray    # 90th percentile
    uncertainty: float         # IQR of first forecast step


@lru_cache(maxsize=1)
def _load_pipeline():
    """Load Chronos pipeline once; cached for the process lifetime."""
    try:
        from chronos import ChronosPipeline  # type: ignore
        import torch
    except ImportError as e:
        raise ImportError(
            "chronos-forecasting not installed.\n"
            "Install with:\n"
            "  pip install git+https://github.com/amazon-science/chronos-forecasting.git\n"
            "or:\n"
            "  pip install chronos-forecasting"
        ) from e

    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info("Loading Chronos model '%s' on %s ...", CHRONOS_MODEL, device)
    pipeline = ChronosPipeline.from_pretrained(
        CHRONOS_MODEL,
        device_map=device,
        torch_dtype=torch.bfloat16,
    )
    logger.info("Chronos model loaded")
    return pipeline


def forecast(close_series: pd.Series) -> ForecastResult:
    """
    Generate a probabilistic forecast for the next FORECAST_HORIZON steps.

    Parameters
    ----------
    close_series : Recent BTC/USDT close prices (at least CONTEXT_LEN values)

    Returns
    -------
    ForecastResult with median, low, high quantile forecasts + uncertainty
    """
    import torch

    if len(close_series) < CONTEXT_LEN:
        raise ValueError(
            f"Need at least {CONTEXT_LEN} close prices; got {len(close_series)}"
        )

    pipeline = _load_pipeline()
    # Use last CONTEXT_LEN bars only
    context = close_series.values[-CONTEXT_LEN:].astype(float)
    context_tensor = torch.tensor(context, dtype=torch.float32).unsqueeze(0)

    # num_samples=20 is enough for median + quantiles; small for CPU speed
    # ponytail: 20 samples, increase to 100 if uncertainty estimates matter more
    forecast_samples = pipeline.predict(
        context_tensor,
        prediction_length=FORECAST_HORIZON,
        num_samples=20,
        limit_prediction_length=False,
    )
    # forecast_samples shape: (batch=1, num_samples, horizon)
    samples = forecast_samples[0].numpy()          # (num_samples, horizon)

    median = np.median(samples, axis=0)
    low_q  = np.percentile(samples, 10, axis=0)
    high_q = np.percentile(samples, 90, axis=0)
    # Uncertainty = IQR at first forecast step (normalised by current price)
    iqr = float(np.percentile(samples[:, 0], 75) - np.percentile(samples[:, 0], 25))
    current_price = float(context[-1])
    uncertainty = iqr / current_price if current_price > 0 else 0.0

    return ForecastResult(median=median, low_q=low_q, high_q=high_q, uncertainty=uncertainty)
