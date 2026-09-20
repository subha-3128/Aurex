"""
Confidence layer — combines XGBoost probability + Chronos agreement + regime.

Produces a single confidence score in [0, 1] that the Risk Shield uses
as a threshold gate.

Formula (weighted average):
    confidence = w_xgb × xgb_max_prob
               + w_dir × direction_agreement
               + w_regime × regime_bonus
"""
from app.regime.detector import REGIME_RISK_MULTIPLIER


# Weights (must sum to 1.0)
W_XGB    = 0.65
W_DIR    = 0.20
W_REGIME = 0.15


def compute_confidence(
    xgb_max_prob:         float,      # from XGBoost predict
    signal:               str,        # "BUY" | "SELL" | "HOLD"
    forecast_direction:   int,        # +1 / -1 / 0 from Chronos
    regime:               str = "SIDEWAYS",
) -> float:
    """
    Compute overall signal confidence.

    Returns a float in [0, 1].
    """
    # Direction agreement: 1.0 if Chronos aligns with signal, 0.5 if neutral, 0.0 if opposite
    if signal == "BUY":
        dir_score = 1.0 if forecast_direction == 1 else (0.5 if forecast_direction == 0 else 0.0)
    elif signal == "SELL":
        dir_score = 1.0 if forecast_direction == -1 else (0.5 if forecast_direction == 0 else 0.0)
    else:
        dir_score = 0.5   # HOLD is neutral

    # Regime bonus: normalise REGIME_RISK_MULTIPLIER to [0, 1]
    regime_mult  = REGIME_RISK_MULTIPLIER.get(regime, 0.75)
    regime_score = regime_mult   # already in [0.3, 1.0] range

    confidence = (
        W_XGB    * xgb_max_prob
        + W_DIR    * dir_score
        + W_REGIME * regime_score
    )
    return round(min(max(confidence, 0.0), 1.0), 4)
