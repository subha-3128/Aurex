"""
Portfolio — tracks positions, equity, and persists state to SQLite.
"""
from __future__ import annotations
import logging
import os
import time
from dataclasses import dataclass, field

from app.database.db import insert_trade, save_portfolio_snapshot

logger = logging.getLogger(__name__)

TAKER_FEE = float(os.getenv("TAKER_FEE", "0.001"))
SLIPPAGE  = float(os.getenv("SLIPPAGE",  "0.0005"))


@dataclass
class OpenPosition:
    symbol:      str
    entry_price: float
    qty:         float        # units of BTC
    size_usd:    float        # USD allocated
    entry_ts:    int          # unix ms
    signal:      str = "BUY"


class Portfolio:
    def __init__(self, initial_capital: float) -> None:
        self.initial_capital  = initial_capital
        self.cash:      float = initial_capital
        self.position:  OpenPosition | None = None
        self.trade_count: int = 0

    @property
    def equity(self) -> float:
        """Mark-to-market equity (needs current price for open position)."""
        return self.cash   # updated by mark_to_market()

    def mark_to_market(self, current_price: float) -> float:
        """Return current equity value."""
        pos_val = (self.position.qty * current_price) if self.position else 0.0
        return self.cash + pos_val

    def open_position(
        self,
        price: float,
        size_usd: float,
        symbol: str = "BTC/USDT",
        ts: int | None = None,
    ) -> float:
        """
        Open a BUY position. Deducts from cash.
        Returns actual fill price (with slippage).
        """
        if self.position is not None:
            logger.warning("Attempted to open position while one is already open — ignored")
            return price

        fill = price * (1 + SLIPPAGE)
        fee  = size_usd * TAKER_FEE
        net  = size_usd - fee
        qty  = net / fill

        self.cash    -= size_usd
        self.position = OpenPosition(
            symbol=symbol,
            entry_price=fill,
            qty=qty,
            size_usd=size_usd,
            entry_ts=ts or int(time.time() * 1000),
        )
        logger.info("OPEN  BUY  @ %.2f  qty=%.6f  size=%.4f  cash=%.4f",
                    fill, qty, size_usd, self.cash)
        return fill

    def close_position(
        self,
        price: float,
        ts: int | None = None,
        extra: dict | None = None,
    ) -> dict:
        """
        Close the open position. Returns a trade result dict.
        """
        if self.position is None:
            raise RuntimeError("No open position to close")

        pos = self.position
        fill = price * (1 - SLIPPAGE)
        exit_fee = pos.qty * fill * TAKER_FEE
        proceeds = pos.qty * fill - exit_fee
        gross_pnl = pos.qty * (fill - pos.entry_price)
        net_pnl   = proceeds - pos.size_usd

        self.cash     += proceeds
        self.position  = None
        self.trade_count += 1

        trade = {
            "timestamp":      ts or int(time.time() * 1000),
            "symbol":         pos.symbol,
            "signal":         "SELL",
            "entry_price":    pos.entry_price,
            "exit_price":     fill,
            "position_size":  pos.size_usd,
            "gross_pnl":      round(gross_pnl, 6),
            "fees":           round(exit_fee, 6),
            "net_pnl":        round(net_pnl, 6),
        }
        if extra:
            trade.update(extra)

        logger.info("CLOSE SELL @ %.2f  net_pnl=%.4f  cash=%.4f",
                    fill, net_pnl, self.cash)
        try:
            insert_trade(trade)
        except Exception as e:
            logger.error("Failed to persist trade: %s", e)

        return trade

    def snapshot(self, current_price: float = 0.0) -> dict:
        equity = self.mark_to_market(current_price)
        return {
            "cash":         round(self.cash, 4),
            "equity":       round(equity, 4),
            "trade_count":  self.trade_count,
            "has_position": self.position is not None,
        }
