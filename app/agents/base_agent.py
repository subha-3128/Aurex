"""
BaseAgent — abstract contract that all 4 AI trading agents inherit.

Each agent owns its own performance ledger and lifecycle state.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# ── Agent Status ──────────────────────────────────────────────────────────────
ACTIVE    = "ACTIVE"      # full trading rights
DEGRADED  = "DEGRADED"    # reduced capital, higher confidence hurdle
DEAD      = "DEAD"        # deactivated, no trades allowed

# ── Reward / Punishment Constants ────────────────────────────────────────────
REWARD_SCALE  = 500.0   # points per unit of return on win
PENALTY_SCALE = 1000.0  # points per unit of return on loss (2× asymmetric)
DEGRADED_THRESHOLD = -50.0
DEAD_THRESHOLD     = -100.0
CAPITAL_FLOOR_PCT  = 0.05   # 5% of allocated = episode over


@dataclass
class Decision:
    action:     str    # "BUY" | "SELL" | "HOLD"
    confidence: float  # 0.0 – 1.0
    rationale:  str    # human-readable reasoning string
    agent_id:   str    = ""
    timestamp:  float  = field(default_factory=time.time)


class BaseAgent:
    """
    Abstract AI trading agent.

    Subclasses must implement:
        decide(context: dict) -> Decision
    """

    agent_id:   str
    name:       str
    description: str

    def __init__(self, agent_id: str, name: str, description: str, allocated_capital: float) -> None:
        self.agent_id   = agent_id
        self.name       = name
        self.description = description

        # Capital ledger
        self.allocated_capital: float = allocated_capital
        self.initial_capital:   float = allocated_capital
        self.cash:              float = allocated_capital
        self.has_position:      bool  = False
        self.position_size:     float = 0.0
        self.position_entry:    float = 0.0
        self.position_qty:      float = 0.0

        # Performance ledger
        self.reward_score: float = 0.0
        self.status:       str   = ACTIVE
        self.trade_count:  int   = 0
        self.wins:         int   = 0
        self.losses:       int   = 0
        self.total_pnl:    float = 0.0
        self.peak_capital: float = allocated_capital
        self.max_drawdown: float = 0.0
        self.last_decision: dict[str, Any] | None = None

        # Dynamic trading parameters based on status
        self._base_confidence_hurdle = 0.60
        self._base_size_pct          = 0.80   # use 80% of cash per trade max

    @property
    def win_rate(self) -> float:
        if self.trade_count == 0:
            return 0.0
        return self.wins / self.trade_count

    @property
    def equity(self) -> float:
        return self.cash

    @property
    def confidence_hurdle(self) -> float:
        """Confidence required to actually trade — rises when DEGRADED."""
        if self.status == DEGRADED:
            return min(0.85, self._base_confidence_hurdle + 0.15)
        return self._base_confidence_hurdle

    @property
    def size_multiplier(self) -> float:
        """Capital fraction usable for a position — reduced when DEGRADED."""
        if self.status == DEGRADED:
            return 0.4
        return 0.8

    def can_trade(self) -> bool:
        return self.status != DEAD

    def decide(self, context: dict[str, Any]) -> Decision:
        raise NotImplementedError("Subclasses must implement decide()")

    def apply_outcome(self, net_pnl: float, trade_size: float) -> None:
        """
        Called after every closed trade. Updates reward score, capital, and status.

        Args:
            net_pnl: realized profit or loss after fees (USD)
            trade_size: original position size (USD)
        """
        if trade_size <= 0:
            return

        # Update cash
        self.cash = max(0.0, self.cash + net_pnl)
        self.total_pnl += net_pnl
        self.trade_count += 1

        # Reward / punishment
        factor = net_pnl / trade_size  # normalized return

        if net_pnl > 0:
            self.wins += 1
            delta = factor * REWARD_SCALE
            logger.info("[%s] REWARD: pnl=+$%.4f  factor=%.4f  delta=+%.2f  score=%.2f → %.2f",
                        self.agent_id, net_pnl, factor, delta, self.reward_score, self.reward_score + delta)
        else:
            self.losses += 1
            delta = factor * PENALTY_SCALE   # factor is negative, so penalty is negative
            logger.warning("[%s] PUNISHMENT: pnl=-$%.4f  factor=%.4f  delta=%.2f  score=%.2f → %.2f",
                           self.agent_id, abs(net_pnl), factor, delta, self.reward_score, self.reward_score + delta)

        self.reward_score += delta

        # Update peak & drawdown
        if self.cash > self.peak_capital:
            self.peak_capital = self.cash
        drawdown = (self.peak_capital - self.cash) / self.peak_capital if self.peak_capital > 0 else 0.0
        self.max_drawdown = max(self.max_drawdown, drawdown)

        # Lifecycle state transitions
        floor = self.initial_capital * CAPITAL_FLOOR_PCT
        old_status = self.status
        if self.cash <= floor or self.reward_score <= DEAD_THRESHOLD:
            self.status = DEAD
        elif self.reward_score <= DEGRADED_THRESHOLD:
            self.status = DEGRADED
        else:
            self.status = ACTIVE

        if self.status != old_status:
            logger.warning("[%s] Status transition: %s → %s  (reward_score=%.2f, cash=%.4f)",
                           self.agent_id, old_status, self.status, self.reward_score, self.cash)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id":         self.agent_id,
            "name":             self.name,
            "description":      self.description,
            "status":           self.status,
            "allocated_capital": self.allocated_capital,
            "cash":             round(self.cash, 4),
            "equity":           round(self.equity, 4),
            "reward_score":     round(self.reward_score, 2),
            "trade_count":      self.trade_count,
            "wins":             self.wins,
            "losses":           self.losses,
            "win_rate_pct":     round(self.win_rate * 100, 1),
            "total_pnl":        round(self.total_pnl, 4),
            "max_drawdown_pct": round(self.max_drawdown * 100, 2),
            "confidence_hurdle": round(self.confidence_hurdle, 2),
            "size_multiplier":   round(self.size_multiplier, 2),
            "has_position":      self.has_position,
            "last_decision":     self.last_decision,
        }
