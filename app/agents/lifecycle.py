"""
AgentLifecycleManager — orchestrates all 4 AI trading agents.

Responsibilities:
  - Initialize agents with proportional capital split
  - Run each agent's decide() cycle with shared market context
  - Route approved decisions to LiveBroker via RiskShield
  - Apply reward/punishment after each trade close
  - Persist agent state to SQLite
  - Rebalance capital when an agent dies
"""
from __future__ import annotations

import logging
import time
from typing import Any

from app.agents.base_agent import BaseAgent, Decision, ACTIVE, DEGRADED, DEAD
from app.agents.quant_agent import QuantAgent
from app.agents.sentiment_agent import SentimentAgent
from app.agents.foundation_agent import FoundationAgent
from app.agents.master_agent import MasterAgent
from app.database.db import save_agent_state, load_agent_states

logger = logging.getLogger(__name__)


class AgentLifecycleManager:
    """
    Manages the full lifecycle of all 4 trading agents:
      Agent A: Quant Analyst
      Agent B: Sentiment Analyst
      Agent C: Foundation AI
      Agent D: Master Brain
    """

    def __init__(self, total_capital: float) -> None:
        self.total_capital = total_capital

        # Capital split: each agent gets an equal share
        per_agent = total_capital / 4.0

        self.agents: list[BaseAgent] = [
            QuantAgent(allocated_capital=per_agent),
            SentimentAgent(allocated_capital=per_agent),
            FoundationAgent(allocated_capital=per_agent),
            MasterAgent(allocated_capital=per_agent),
        ]

        # Restore persisted state if available
        self._restore_state()
        logger.info("AgentLifecycleManager initialized: %d agents, $%.2f each",
                    len(self.agents), per_agent)

    @property
    def active_agents(self) -> list[BaseAgent]:
        return [a for a in self.agents if a.status != DEAD]

    @property
    def total_equity(self) -> float:
        return sum(a.equity for a in self.agents)

    def get_agent(self, agent_id: str) -> BaseAgent | None:
        return next((a for a in self.agents if a.agent_id == agent_id), None)

    def run_cycle(self, context: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Run one full decision cycle for all active agents.

        Args:
            context: shared market data (indicators, research, price, regime, df)

        Returns:
            List of decision dicts, one per active agent.
        """
        peer_agents    = [a for a in self.agents if a.status != DEAD and a.agent_id != "agent_master"]
        peer_decisions = []

        cycle_results = []

        # ── Run specialist agents (A, B, C) first ────────────────────────────
        for agent in peer_agents:
            try:
                dec = agent.decide(context)
                agent.last_decision = dec.__dict__
                peer_decisions.append(dec.__dict__)
                cycle_results.append({
                    "agent_id":   agent.agent_id,
                    "name":       agent.name,
                    "action":     dec.action,
                    "confidence": dec.confidence,
                    "rationale":  dec.rationale,
                    "status":     agent.status,
                })
                logger.info("[%s] Decision: %s (conf=%.2f) | %s",
                            agent.agent_id, dec.action, dec.confidence, dec.rationale[:80])
            except Exception as e:
                logger.error("[%s] decide() failed: %s", agent.agent_id, e)
                cycle_results.append({
                    "agent_id": agent.agent_id, "action": "HOLD",
                    "confidence": 0.5, "status": agent.status, "error": str(e)
                })

        # ── Run Master Brain with peer decisions as context ────────────────────
        master = self.get_agent("agent_master")
        if master and master.status != DEAD:
            master_context = {
                **context,
                "peer_decisions": peer_decisions,
                "peer_agents":    peer_agents,
            }
            try:
                master_dec = master.decide(master_context)
                master.last_decision = master_dec.__dict__
                cycle_results.append({
                    "agent_id":   master.agent_id,
                    "name":       master.name,
                    "action":     master_dec.action,
                    "confidence": master_dec.confidence,
                    "rationale":  master_dec.rationale,
                    "status":     master.status,
                })
                logger.info("[%s] Master decision: %s (conf=%.2f)",
                            master.agent_id, master_dec.action, master_dec.confidence)
            except Exception as e:
                logger.error("[master] decide() failed: %s", e)

        # Persist state
        self._persist_state()
        return cycle_results

    def apply_trade_outcome(
        self, agent_id: str, net_pnl: float, trade_size: float,
        entry_price: float = 0.0, exit_price: float = 0.0
    ) -> None:
        """
        Apply reward or punishment to a specific agent after a closed trade.
        Rebalances capital if an agent dies.
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return

        old_status = agent.status
        agent.apply_outcome(net_pnl, trade_size)
        agent.has_position = False
        agent.position_size = 0.0
        agent.position_entry = 0.0
        agent.position_qty = 0.0

        # If agent just died, rebalance capital to survivors
        if agent.status == DEAD and old_status != DEAD:
            self._rebalance_capital()

        self._persist_state()

    def record_position_open(
        self, agent_id: str, price: float, size_usd: float, qty: float
    ) -> None:
        """Record that an agent has opened a position."""
        agent = self.get_agent(agent_id)
        if agent:
            agent.has_position  = True
            agent.position_size = size_usd
            agent.position_entry = price
            agent.position_qty  = qty
            agent.cash -= size_usd

    def record_position_close(self, agent_id: str, proceeds: float) -> None:
        """Update cash when position closes (before apply_trade_outcome)."""
        agent = self.get_agent(agent_id)
        if agent:
            agent.has_position  = False
            agent.position_size = 0.0
            agent.cash += proceeds

    def _rebalance_capital(self) -> None:
        """
        When an agent dies, recover its remaining cash and
        distribute it proportionally among surviving agents.
        """
        dead_cash = sum(a.cash for a in self.agents if a.status == DEAD and a.cash > 0)
        if dead_cash <= 0:
            return
        # Zero out dead agents' cash (capital reclaimed)
        for a in self.agents:
            if a.status == DEAD:
                a.cash = 0.0

        survivors = [a for a in self.agents if a.status != DEAD]
        if not survivors:
            logger.warning("All agents are DEAD. No capital to rebalance.")
            return

        per_survivor = dead_cash / len(survivors)
        for a in survivors:
            a.cash += per_survivor
            logger.info("[lifecycle] Rebalanced +$%.2f to %s (new cash: $%.2f)",
                        per_survivor, a.agent_id, a.cash)

    def _persist_state(self) -> None:
        for agent in self.agents:
            try:
                save_agent_state(agent.to_dict())
            except Exception as e:
                logger.error("Failed to persist agent state [%s]: %s", agent.agent_id, e)

    def _restore_state(self) -> None:
        try:
            saved = load_agent_states()
            for record in saved:
                agent = self.get_agent(record["agent_id"])
                if agent:
                    agent.reward_score = record.get("reward_score", 0.0)
                    agent.status       = record.get("status", ACTIVE)
                    agent.cash         = record.get("cash", agent.cash)
                    agent.trade_count  = record.get("trade_count", 0)
                    agent.wins         = record.get("wins", 0)
                    agent.losses       = record.get("losses", 0)
                    agent.total_pnl    = record.get("total_pnl", 0.0)
                    agent.has_position = record.get("has_position", False)
                    logger.info("Restored %s: status=%s, score=%.2f, cash=$%.2f",
                                agent.agent_id, agent.status, agent.reward_score, agent.cash)
        except Exception as e:
            logger.debug("No saved agent state to restore: %s", e)

    def all_to_dict(self) -> list[dict]:
        return [a.to_dict() for a in self.agents]


if __name__ == "__main__":
    import json, logging
    logging.basicConfig(level=logging.INFO)
    mgr = AgentLifecycleManager(total_capital=50.0)
    print(json.dumps(mgr.all_to_dict(), indent=2))
