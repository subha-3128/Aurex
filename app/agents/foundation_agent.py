"""
Agent C — Foundation AI

Strategy: probabilistic time-series forecasting + ML classification.
Primary: Chronos-Bolt zero-shot foundation model price path prediction.
Fallback: XGBoost Triple-Barrier directional classifier.
Gating: Secondary meta-labeler probability gate.
"""
from __future__ import annotations

import logging
from typing import Any

from app.agents.base_agent import BaseAgent, Decision

logger = logging.getLogger(__name__)


class FoundationAgent(BaseAgent):
    """
    AI Foundation model trading agent.
    Reads: Chronos-Bolt zero-shot forecast + XGBoost Triple-Barrier probabilities.
    """

    def __init__(self, allocated_capital: float) -> None:
        super().__init__(
            agent_id    = "agent_foundation",
            name        = "Foundation AI",
            description = "Amazon Chronos-Bolt zero-shot time-series forecasting combined with XGBoost Triple-Barrier classifier and Meta-Labeler precision gating.",
            allocated_capital = allocated_capital,
        )
        self._base_confidence_hurdle = 0.65  # Higher bar — pure ML confidence

    def decide(self, context: dict[str, Any]) -> Decision:
        row    = context.get("indicators", {})
        price  = context.get("price", 0.0)
        regime = context.get("regime", "SIDEWAYS")
        df     = context.get("df", None)

        buy_prob  = 0.33
        sell_prob = 0.33
        hold_prob = 0.34
        meta_confidence = 0.60
        forecast_dir = 0
        reasons = []

        # ── XGBoost prediction ────────────────────────────────────────────────
        try:
            from app.ai.predict import predict
            pred = predict(row)
            buy_prob        = pred.get("buy_prob", 0.33)
            sell_prob       = pred.get("sell_prob", 0.33)
            hold_prob       = pred.get("hold_prob", 0.34)
            meta_confidence = pred.get("meta_confidence", 0.60)
            reasons.append(f"XGBoost: BUY={buy_prob:.1%} SELL={sell_prob:.1%} META={meta_confidence:.1%}")
        except Exception as e:
            logger.debug("XGBoost unavailable: %s", e)

        # ── Chronos-Bolt forecast ──────────────────────────────────────────────
        try:
            if df is not None and len(df) >= 32:
                from app.forecasting.chronos_model import forecast
                from app.forecasting.forecast_features import extract_forecast_features
                fc = forecast(df["close"])
                fc_feats = extract_forecast_features(fc, price)
                forecast_dir = fc_feats.get("forecast_direction", 0)
                fc_pct = fc_feats.get("expected_return_pct", 0.0)
                reasons.append(f"Chronos: dir={forecast_dir:+d} expected={fc_pct:.2f}%")
        except Exception as e:
            logger.debug("Chronos unavailable: %s", e)

        # ── Confidence synthesis ──────────────────────────────────────────────
        # Primary signal from XGBoost probabilities
        if buy_prob > sell_prob and buy_prob > hold_prob:
            primary = "BUY"
            base_conf = buy_prob
        elif sell_prob > buy_prob and sell_prob > hold_prob:
            primary = "SELL"
            base_conf = sell_prob
        else:
            primary = "HOLD"
            base_conf = hold_prob

        # Chronos alignment bonus
        if forecast_dir == 1 and primary == "BUY":
            base_conf = min(base_conf + 0.08, 0.95)
            reasons.append("Chronos confirms bullish forecast")
        elif forecast_dir == -1 and primary == "SELL":
            base_conf = min(base_conf + 0.08, 0.95)
            reasons.append("Chronos confirms bearish forecast")
        elif forecast_dir != 0 and ((forecast_dir == 1 and primary == "SELL") or (forecast_dir == -1 and primary == "BUY")):
            base_conf = base_conf * 0.75
            reasons.append("Chronos CONTRADICTS signal — confidence reduced")

        # Meta-labeler gating: prune entries with low net-profit probability
        if primary in ("BUY", "SELL") and meta_confidence < 0.45:
            primary = "HOLD"
            reasons.append(f"Meta-labeler pruned signal: P(profit)={meta_confidence:.1%} < 45%")
            base_conf = max(base_conf, 0.50)

        # Final action
        if primary == "BUY" and not self.has_position:
            action = "BUY"
        elif primary == "SELL" and self.has_position:
            action = "SELL"
        else:
            action = "HOLD"
            base_conf = max(base_conf, 0.50)

        rationale = f"[Foundation] " + " | ".join(reasons[:3])

        return Decision(
            action     = action,
            confidence = round(base_conf, 3),
            rationale  = rationale,
            agent_id   = self.agent_id,
        )
