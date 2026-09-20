"""
Agent B — Sentiment Analyst

Strategy: internet research-driven contrarian and momentum sentiment trading.
Reads: Fear & Greed Index, CoinGecko 24h change, crypto news headlines.
Philosophy: trade against extremes, follow confirmed momentum in neutral zones.
"""
from __future__ import annotations

import logging
from typing import Any

from app.agents.base_agent import BaseAgent, Decision

logger = logging.getLogger(__name__)


class SentimentAgent(BaseAgent):
    """
    Internet-research-driven sentiment trading agent.
    Reads: Fear & Greed, CoinGecko momentum, news headline sentiment.
    """

    def __init__(self, allocated_capital: float) -> None:
        super().__init__(
            agent_id    = "agent_sentiment",
            name        = "Sentiment Analyst",
            description = "Contrarian and momentum trading driven by Fear & Greed Index, CoinGecko 24h market data, and live crypto news headline sentiment.",
            allocated_capital = allocated_capital,
        )

    def decide(self, context: dict[str, Any]) -> Decision:
        research = context.get("research", {})
        regime   = context.get("regime", "SIDEWAYS")
        row      = context.get("indicators", {})

        # ── Sentiment sources ─────────────────────────────────────────────────
        fg        = research.get("fear_greed", {})
        cg        = research.get("coingecko", {})
        news      = research.get("news", {})

        fg_score    = fg.get("score", 50)
        fg_label    = fg.get("label", "Neutral")
        fg_sentiment = fg.get("sentiment", 0.0)  # -1 to +1 (contrarian)

        cg_change   = cg.get("change_24h_pct", 0.0)
        cg_momentum = cg.get("momentum", 0.0)    # normalized -1 to +1

        news_sentiment = news.get("news_sentiment", 0.0)  # -1 to +1

        # RSI for confirmation
        rsi = float(row.get("rsi", 50.0) or 50.0)

        # ── Reasoning ─────────────────────────────────────────────────────────
        reasons = []
        buy_signals  = 0
        sell_signals = 0

        # Fear & Greed (contrarian signal)
        if fg_score <= 20:
            buy_signals += 3
            reasons.append(f"Extreme Fear (F&G={fg_score}) — contrarian BUY signal")
        elif fg_score <= 35:
            buy_signals += 2
            reasons.append(f"Fear zone (F&G={fg_score}) — moderate BUY sentiment")
        elif fg_score >= 80:
            sell_signals += 3
            reasons.append(f"Extreme Greed (F&G={fg_score}) — contrarian SELL signal")
        elif fg_score >= 65:
            sell_signals += 2
            reasons.append(f"Greed zone (F&G={fg_score}) — moderate SELL sentiment")
        else:
            reasons.append(f"Neutral Fear & Greed (F&G={fg_score})")

        # CoinGecko 24h price momentum
        if cg_change > 3.0:
            buy_signals += 1
            reasons.append(f"CoinGecko 24h +{cg_change:.1f}% — positive momentum")
        elif cg_change < -3.0:
            sell_signals += 1
            reasons.append(f"CoinGecko 24h {cg_change:.1f}% — negative momentum")

        # News sentiment
        if news_sentiment > 0.4:
            buy_signals += 1
            reasons.append(f"News bullish ({news.get('bullish_count',0)} bull vs {news.get('bearish_count',0)} bear headlines)")
        elif news_sentiment < -0.4:
            sell_signals += 1
            reasons.append(f"News bearish ({news.get('bullish_count',0)} bull vs {news.get('bearish_count',0)} bear headlines)")

        # RSI confirmation in extreme regimes
        if buy_signals > sell_signals and rsi < 60:
            buy_signals += 1
            reasons.append(f"RSI {rsi:.1f} confirms bullish entry room")
        elif sell_signals > buy_signals and rsi > 45:
            sell_signals += 1
            reasons.append(f"RSI {rsi:.1f} confirms exit territory")

        # ── Final decision ────────────────────────────────────────────────────
        net   = buy_signals - sell_signals
        total = buy_signals + sell_signals or 1
        confidence = min(abs(net) / (total + 1), 0.92)

        if net >= 3 and not self.has_position:
            action = "BUY"
        elif net <= -3 and self.has_position:
            action = "SELL"
        elif net >= 2 and not self.has_position and confidence >= 0.60:
            action = "BUY"
        elif net <= -2 and self.has_position:
            action = "SELL"
        else:
            action = "HOLD"
            confidence = max(confidence, 0.45)

        rationale = f"[Sentiment] F&G={fg_score} ({fg_label}) | 24h={cg_change:.1f}% | News={news_sentiment:.2f} | " + " | ".join(reasons[:2])

        return Decision(
            action     = action,
            confidence = round(confidence, 3),
            rationale  = rationale,
            agent_id   = self.agent_id,
        )
