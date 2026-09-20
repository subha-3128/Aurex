"""
Agent A — Quant Analyst

Strategy: pure technical analysis + Binance orderbook depth research.
Signals are generated from RSI, EMA crossover, MACD, ATR, and
bid/ask volume imbalance from the live orderbook.
"""
from __future__ import annotations

import logging
from typing import Any

from app.agents.base_agent import BaseAgent, Decision

logger = logging.getLogger(__name__)


class QuantAgent(BaseAgent):
    """
    Systematic rule-based technical trading agent.
    Reads: OHLCV indicators (RSI, EMA, MACD, ATR) + Binance orderbook imbalance.
    """

    def __init__(self, allocated_capital: float) -> None:
        super().__init__(
            agent_id    = "agent_quant",
            name        = "Quant Analyst",
            description = "Technical analysis using RSI, EMA crossovers, MACD momentum, ATR volatility, and live Binance orderbook bid/ask imbalance.",
            allocated_capital = allocated_capital,
        )

    def decide(self, context: dict[str, Any]) -> Decision:
        """
        Decision logic based on technical indicators and orderbook depth.
        Returns Decision(BUY|SELL|HOLD, confidence, rationale).
        """
        row      = context.get("indicators", {})
        research = context.get("research", {})
        regime   = context.get("regime", "SIDEWAYS")
        price    = context.get("price", 0.0)

        # ── Indicator signals ─────────────────────────────────────────────────
        rsi     = float(row.get("rsi", 50.0) or 50.0)
        ema9    = float(row.get("ema_9", price) or price)
        ema21   = float(row.get("ema_21", price) or price)
        ema50   = float(row.get("ema_50", price) or price)
        macd    = float(row.get("macd", 0.0) or 0.0)
        macd_s  = float(row.get("macd_signal", 0.0) or 0.0)
        atr_pct = float(row.get("atr_pct", 0.02) or 0.02)

        # ── Orderbook research ────────────────────────────────────────────────
        ob        = research.get("orderbook", {})
        imbalance = float(ob.get("imbalance", 0.0) or 0.0)  # +1 = buy pressure, -1 = sell pressure

        # ── Score individual signals ──────────────────────────────────────────
        buy_signals  = 0
        sell_signals = 0
        reasons      = []

        # RSI
        if rsi < 30:
            buy_signals += 2
            reasons.append(f"RSI {rsi:.1f} oversold (strong buy)")
        elif rsi < 45:
            buy_signals += 1
            reasons.append(f"RSI {rsi:.1f} below midline (mild buy)")
        elif rsi > 70:
            sell_signals += 2
            reasons.append(f"RSI {rsi:.1f} overbought (strong sell)")
        elif rsi > 55:
            sell_signals += 1
            reasons.append(f"RSI {rsi:.1f} above midline (mild sell)")

        # EMA crossover
        if ema9 > ema21 > ema50:
            buy_signals += 2
            reasons.append("EMA9 > EMA21 > EMA50: full bullish alignment")
        elif ema9 > ema21:
            buy_signals += 1
            reasons.append("EMA9 > EMA21: short-term bullish crossover")
        elif ema9 < ema21 < ema50:
            sell_signals += 2
            reasons.append("EMA9 < EMA21 < EMA50: full bearish alignment")
        elif ema9 < ema21:
            sell_signals += 1
            reasons.append("EMA9 < EMA21: short-term bearish crossover")

        # MACD
        if macd > macd_s and macd > 0:
            buy_signals += 1
            reasons.append("MACD above signal and positive (bullish momentum)")
        elif macd < macd_s and macd < 0:
            sell_signals += 1
            reasons.append("MACD below signal and negative (bearish momentum)")

        # Orderbook imbalance
        if imbalance > 0.20:
            buy_signals += 1
            reasons.append(f"Orderbook bid/ask imbalance +{imbalance:.2f} (buy wall dominates)")
        elif imbalance < -0.20:
            sell_signals += 1
            reasons.append(f"Orderbook bid/ask imbalance {imbalance:.2f} (ask wall dominates)")

        # Volatility filter: avoid trading in extreme ATR
        if atr_pct > 0.05 and regime == "HIGH_VOL":
            reasons.append(f"High volatility ATR={atr_pct:.2%} — signal confidence reduced")
            total = buy_signals + sell_signals or 1
            confidence_cap = 0.60
        else:
            total = buy_signals + sell_signals or 1
            confidence_cap = 1.0

        # ── Final decision ────────────────────────────────────────────────────
        net = buy_signals - sell_signals
        raw_confidence = abs(net) / (total + 2)  # dampened
        confidence = min(raw_confidence, confidence_cap)

        if net >= 2 and not self.has_position:
            action = "BUY"
        elif net <= -2 and self.has_position:
            action = "SELL"
        elif net <= -1 and self.has_position and atr_pct < 0.02:
            action = "SELL"
        else:
            action = "HOLD"
            confidence = max(confidence, 0.50)

        rationale = f"[Quant] Buy={buy_signals} Sell={sell_signals} Net={net:+d} | " + " | ".join(reasons[:3])

        return Decision(
            action     = action,
            confidence = round(confidence, 3),
            rationale  = rationale,
            agent_id   = self.agent_id,
        )
