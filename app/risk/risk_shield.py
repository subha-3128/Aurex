"""
Risk Shield — deterministic safety layer between AI signals and execution.

The AI CANNOT override these rules.
All rules are pure logic: no ML, no probability, no model calls.

Rules (research defaults — configure via .env):
- Max position size: MAX_RISK_PER_TRADE × current capital
- Max daily loss: MAX_DAILY_LOSS × initial capital
- Max open positions: 1
- Emergency stop: can be triggered externally (file-based flag)
- Min confidence threshold for signal acceptance
"""
import logging
import os
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

MAX_RISK_PER_TRADE   = float(os.getenv("MAX_RISK_PER_TRADE",   "0.01"))
MAX_DAILY_LOSS       = float(os.getenv("MAX_DAILY_LOSS",       "0.04"))
MAX_OPEN_POSITIONS   = int(os.getenv("MAX_OPEN_POSITIONS",     "1"))
TAKER_FEE            = float(os.getenv("TAKER_FEE",            "0.001"))
MIN_CONFIDENCE       = float(os.getenv("MIN_CONFIDENCE",        "0.55"))
MIN_NOTIONAL         = float(os.getenv("MIN_NOTIONAL_USD",      "10.0"))
LIVE_TRADING_ENABLED = os.getenv("LIVE_TRADING_ENABLED", "false").lower() == "true"

# Emergency stop flag file — touch this file to halt all new orders
EMERGENCY_FLAG = Path(os.getenv("EMERGENCY_FLAG", "EMERGENCY_STOP"))


@dataclass
class ShieldResult:
    allowed:       bool
    approved_size: float   # USD — 0.0 if rejected
    reason:        str


class RiskShield:
    """
    Stateful risk shield.

    State it tracks:
      - daily_loss   : cumulative net P/L today (negative = loss)
      - open_trades  : number of currently open positions
      - initial_capital : reference capital for daily-loss calculation
    """

    def __init__(self, initial_capital: float) -> None:
        self.initial_capital = initial_capital
        self.daily_loss: float = 0.0
        self.open_trades: int  = 0

    # ── Public API ────────────────────────────────────────────────────────────

    def check(
        self,
        signal: str,              # "BUY" | "SELL" | "HOLD"
        confidence: float,        # 0.0 – 1.0
        current_capital: float,
        atr_pct: float = 0.0,     # normalised ATR (for volatility check)
    ) -> ShieldResult:
        """
        Evaluate whether to allow a proposed trade.

        Returns ShieldResult(allowed, approved_size, reason).
        """
        # HOLD never needs approval
        if signal == "HOLD":
            return ShieldResult(True, 0.0, "HOLD — no trade")

        # ── Emergency stop ────────────────────────────────────────────────────
        if EMERGENCY_FLAG.exists():
            return ShieldResult(False, 0.0, "EMERGENCY STOP active")

        # ── Daily loss limit ──────────────────────────────────────────────────
        daily_loss_limit = self.initial_capital * MAX_DAILY_LOSS
        if self.daily_loss <= -daily_loss_limit:
            return ShieldResult(
                False, 0.0,
                f"Daily loss limit reached ({self.daily_loss:.2f} / -{daily_loss_limit:.2f})"
            )

        # ── Open positions ────────────────────────────────────────────────────
        if signal == "BUY" and self.open_trades >= MAX_OPEN_POSITIONS:
            return ShieldResult(
                False, 0.0,
                f"Max open positions ({MAX_OPEN_POSITIONS}) already reached"
            )

        # ── Minimum confidence ────────────────────────────────────────────────
        if confidence < MIN_CONFIDENCE:
            return ShieldResult(
                False, 0.0,
                f"Confidence {confidence:.2%} below minimum {MIN_CONFIDENCE:.2%}"
            )

        # ── Extreme volatility guard (ATR > 5% of price → halve size) ────────
        size = current_capital * MAX_RISK_PER_TRADE
        if atr_pct > 0.05:
            size *= 0.5
            logger.warning("High volatility (ATR=%.2f%%) — position halved", atr_pct * 100)

        # ── Capital & Notional Guard ──────────────────────────────────────────
        size = min(size, current_capital * 0.95)   # never stake more than 95% of capital
        if LIVE_TRADING_ENABLED:
            if current_capital * 0.95 < MIN_NOTIONAL:
                return ShieldResult(
                    False, 0.0,
                    f"Capital ${current_capital:.2f} is below exchange min notional ${MIN_NOTIONAL:.2f}"
                )
            if size < MIN_NOTIONAL:
                size = MIN_NOTIONAL

        if size <= 0:
            return ShieldResult(False, 0.0, "Insufficient capital")

        # ── Approved ──────────────────────────────────────────────────────────
        logger.info("Risk Shield APPROVED: %s  size=%.4f  confidence=%.2f",
                    signal, size, confidence)
        return ShieldResult(True, round(size, 6), "Approved")

    # ── State updates (called by portfolio/execution layer) ───────────────────

    def record_trade_open(self) -> None:
        self.open_trades += 1

    def record_trade_close(self, net_pnl: float) -> None:
        self.open_trades = max(0, self.open_trades - 1)
        self.daily_loss += net_pnl

    def reset_daily(self) -> None:
        """Call at the start of each trading day."""
        self.daily_loss = 0.0
        logger.info("Risk Shield: daily loss counter reset")

    def trigger_emergency_stop(self) -> None:
        """Write emergency flag file — stops all new orders."""
        EMERGENCY_FLAG.touch()
        logger.critical("EMERGENCY STOP triggered — no new orders will be placed")

    def clear_emergency_stop(self) -> None:
        """Remove emergency flag (manual recovery)."""
        if EMERGENCY_FLAG.exists():
            EMERGENCY_FLAG.unlink()
        logger.info("Emergency stop cleared")
