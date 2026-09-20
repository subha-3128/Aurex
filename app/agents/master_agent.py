"""
Agent D — Master Brain

Strategy: democratic aggregation of all other active agent signals,
weighted by each agent's current reward score (performance-weighted voting).
The Master Brain does not generate its own independent signals —
it is a meta-agent that synthesizes and arbitrates.
"""
from __future__ import annotations

import logging
from typing import Any

from app.agents.base_agent import BaseAgent, Decision, DEAD

logger = logging.getLogger(__name__)


class MasterAgent(BaseAgent):
    """
    Performance-weighted meta-agent that aggregates decisions from all other agents.
    Agents with higher reward scores get proportionally more voting weight.
    Minimum consensus required: at least 2 active agent votes for a non-HOLD action.
    """

    def __init__(self, allocated_capital: float) -> None:
        super().__init__(
            agent_id    = "agent_master",
            name        = "Master Brain",
            description = "Performance-weighted democratic aggregator — synthesizes decisions from all active agents, giving more influence to higher-scoring models.",
            allocated_capital = allocated_capital,
        )
        self._base_confidence_hurdle = 0.62

    def decide(self, context: dict[str, Any]) -> Decision:
        peer_decisions: list[dict] = context.get("peer_decisions", [])
        peer_agents:    list       = context.get("peer_agents", [])
        regime = context.get("regime", "SIDEWAYS")

        # Filter to active agents only
        active_peers = [(a, d) for a, d in zip(peer_agents, peer_decisions)
                        if a.status != DEAD]

        if not active_peers:
            return Decision(
                action="HOLD", confidence=0.50,
                rationale="[Master] No active peer agents — defaulting to HOLD",
                agent_id=self.agent_id,
            )

        # ── Weighted voting ───────────────────────────────────────────────────
        buy_weight  = 0.0
        sell_weight = 0.0
        hold_weight = 0.0
        reasons     = []

        for agent, dec in active_peers:
            # Weight = max(reward_score, 1) so that new agents (score=0) still vote
            raw_weight = max(agent.reward_score + 100.0, 1.0)  # shift so dead zone < 0 still counts low
            vote_weight = raw_weight * dec["confidence"]

            if dec["action"] == "BUY":
                buy_weight  += vote_weight
                reasons.append(f"{agent.name}: BUY ({dec['confidence']:.0%}, w={raw_weight:.0f})")
            elif dec["action"] == "SELL":
                sell_weight += vote_weight
                reasons.append(f"{agent.name}: SELL ({dec['confidence']:.0%}, w={raw_weight:.0f})")
            else:
                hold_weight += vote_weight

        total_weight = buy_weight + sell_weight + hold_weight or 1.0

        buy_frac  = buy_weight  / total_weight
        sell_frac = sell_weight / total_weight

        # Count how many distinct agents voted for the leading action
        buy_voter_count  = sum(1 for a, d in active_peers if d["action"] == "BUY")
        sell_voter_count = sum(1 for a, d in active_peers if d["action"] == "SELL")

        # Require at least 2 agents for a non-HOLD action
        if buy_frac > sell_frac and buy_frac > 0.45 and buy_voter_count >= 2 and not self.has_position:
            action     = "BUY"
            confidence = min(buy_frac * 1.1, 0.92)
        elif sell_frac > buy_frac and sell_frac > 0.45 and sell_voter_count >= 2 and self.has_position:
            action     = "SELL"
            confidence = min(sell_frac * 1.1, 0.92)
        else:
            action     = "HOLD"
            confidence = 0.50

        # Reduce conviction in HIGH_VOL regime
        if regime == "HIGH_VOL":
            confidence *= 0.90

        rationale = f"[Master] BUY={buy_frac:.0%} SELL={sell_frac:.0%} HOLD={1-buy_frac-sell_frac:.0%} | " + " | ".join(reasons[:3])

        return Decision(
            action     = action,
            confidence = round(confidence, 3),
            rationale  = rationale,
            agent_id   = self.agent_id,
        )
