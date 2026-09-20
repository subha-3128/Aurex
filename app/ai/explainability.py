from __future__ import annotations

"""
AI Explainability Engine — transparent decision audits.

Generates complete, human-understandable reasoning for every proposed trade:
- Multi-signal factor breakdown
- Risk personality and stress state
- Sizing calculation
- Risk Shield gatekeeper verdict (Approved / Blocked with explicit rule)
"""
import pandas as pd
from typing import TypedDict


class DecisionExplanation(TypedDict):
    decision_id: str
    action: str                    # BUY / SELL / HOLD
    confidence_pct: float
    reasons: list[str]
    signals: dict[str, str | float]
    risk_profile: dict[str, str | float]
    shield_verdict: str            # APPROVED / REJECTED
    shield_reason: str
    proposed_size_usd: float
    approved_size_usd: float


def build_explanation(
    row: pd.Series,
    signal: str,
    confidence: float,
    buy_prob: float,
    sell_prob: float,
    regime: str,
    forecast_dir: int,
    personality: dict,
    stress: dict,
    shield_allowed: bool,
    shield_reason: str,
    proposed_size: float,
    approved_size: float,
) -> DecisionExplanation:
    """
    Construct a structured, explainable decision audit.
    """
    reasons = []
    
    # 1. AI Forecasting rationale
    if forecast_dir == 1:
        reasons.append("Chronos-2 zero-shot forecast is Bullish (+1).")
    elif forecast_dir == -1:
        reasons.append("Chronos-2 zero-shot forecast is Bearish (-1).")
    else:
        reasons.append("Chronos-2 forecast indicates Neutral consolidation.")

    # 2. XGBoost decision
    reasons.append(f"XGBoost classifier estimated {buy_prob*100:.1f}% BUY / {sell_prob*100:.1f}% SELL probability.")

    # 3. Technical indicators
    rsi = float(row.get("rsi", 50.0))
    if rsi < 35:
        reasons.append(f"RSI ({rsi:.1f}) indicates oversold rebound potential.")
    elif rsi > 70:
        reasons.append(f"RSI ({rsi:.1f}) indicates overbought saturation.")
    else:
        reasons.append(f"RSI ({rsi:.1f}) sits in healthy momentum range.")

    ema9 = float(row.get("ema_9", 0.0))
    ema21 = float(row.get("ema_21", 0.0))
    if ema9 > ema21:
        reasons.append("Short-term EMA9 is positioned above EMA21 (Bullish trend alignment).")
    else:
        reasons.append("Short-term EMA9 is positioned below EMA21 (Bearish trend alignment).")

    # 4. Regime & Stress
    reasons.append(f"Market classified as {regime.replace('_', ' ')} with {stress.get('level')} Stress ({stress.get('score')} pts).")
    reasons.append(f"AI Risk Personality mode is set to '{personality.get('mode')}': {personality.get('rationale')}")

    # Build signal dictionary
    signals = {
        "chronos_forecast": "Bullish" if forecast_dir == 1 else "Bearish" if forecast_dir == -1 else "Neutral",
        "xgb_buy_prob": round(buy_prob * 100, 1),
        "xgb_sell_prob": round(sell_prob * 100, 1),
        "rsi": round(rsi, 1),
        "ema_trend": "Bullish" if ema9 > ema21 else "Bearish",
        "regime": regime,
        "volatility": "High" if float(row.get("atr_pct", 0)) > 0.02 else "Moderate",
    }

    risk_profile = {
        "personality_mode": personality.get("mode", "Normal"),
        "stress_level": stress.get("level", "LOW"),
        "stress_score": stress.get("score", 0.0),
        "size_multiplier": personality.get("multiplier", 1.0),
    }

    return {
        "decision_id": f"DEC-{int(row.name if isinstance(row.name, (int, float)) else 1001)}",
        "action": signal,
        "confidence_pct": round(confidence * 100, 1),
        "reasons": reasons,
        "signals": signals,
        "risk_profile": risk_profile,
        "shield_verdict": "APPROVED" if shield_allowed else "REJECTED",
        "shield_reason": shield_reason,
        "proposed_size_usd": round(proposed_size, 2),
        "approved_size_usd": round(approved_size, 2),
    }
