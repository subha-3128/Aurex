"""
Live Broker — executes real spot orders on Binance via CCXT.

Supports:
  - Live Binance (real money)
  - Binance Spot Testnet (sandbox mode)
  - Balance synchronization
  - Exchange filters (MIN_NOTIONAL, LOT_SIZE, PRICE_FILTER)
  - Safe error handling & rate limit protection
"""
from __future__ import annotations
import logging
import math
import time
from typing import Any, Dict, Optional

import ccxt

logger = logging.getLogger(__name__)


class LiveBroker:
    """
    CCXT-based execution broker for Binance Spot.

    Maintains identical interface to PaperBroker:
      fill_buy(price, size_usd)  → float (actual fill price)
      fill_sell(price, qty)      → float (actual fill price)
      get_balance()              → dict (wallet balances)
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        sandbox: bool = False,
        symbol: str = "BTC/USDT",
        max_allocated_capital: float = 50.0,
    ) -> None:
        self.api_key = api_key
        self.api_secret = api_secret
        self.sandbox = sandbox
        self.symbol = symbol
        self.max_allocated_capital = max_allocated_capital

        self.exchange: ccxt.binance = ccxt.binance({
            "apiKey": self.api_key,
            "secret": self.api_secret,
            "enableRateLimit": True,
            "options": {
                "defaultType": "spot",
                "adjustForTimeDifference": True,
            },
        })

        if self.sandbox:
            self.exchange.set_sandbox_mode(True)
            logger.info("[LIVE BROKER] Initialized in SANDBOX / TESTNET mode")
        else:
            logger.warning("[LIVE BROKER] INITIALIZED IN REAL MONEY PRODUCTION MODE")

        # Cache symbol rules
        self._markets_loaded = False
        self.min_notional = 10.0
        self.min_qty = 0.00001
        self.step_size = 0.00001
        self.tick_size = 0.01

    def load_markets(self) -> None:
        """Load and cache exchange market filters for the trading pair."""
        if self._markets_loaded:
            return
        try:
            markets = self.exchange.load_markets()
            if self.symbol in markets:
                m = markets[self.symbol]
                limits = m.get("limits", {})
                cost_limits = limits.get("cost", {})
                amount_limits = limits.get("amount", {})
                price_limits = limits.get("price", {})

                self.min_notional = float(cost_limits.get("min", 10.0) or 10.0)
                self.min_qty = float(amount_limits.get("min", 0.00001) or 0.00001)
                
                precision = m.get("precision", {})
                amount_prec = precision.get("amount", 5)
                self.step_size = 10 ** (-amount_prec) if isinstance(amount_prec, int) else float(amount_prec or 0.00001)

                price_prec = precision.get("price", 2)
                self.tick_size = 10 ** (-price_prec) if isinstance(price_prec, int) else float(price_prec or 0.01)

                self._markets_loaded = True
                logger.info("[LIVE BROKER] %s filters loaded: min_notional=$%.2f, step_size=%.6f, min_qty=%.6f",
                            self.symbol, self.min_notional, self.step_size, self.min_qty)
        except Exception as e:
            logger.error("[LIVE BROKER] Failed to load market filters: %s", e)

    def verify_connection(self) -> Dict[str, Any]:
        """
        Verify API credentials and read permissions without placing orders.
        """
        try:
            balance = self.exchange.fetch_balance()
            total_usdt = float(balance.get("total", {}).get("USDT", 0.0) or 0.0)
            free_usdt = float(balance.get("free", {}).get("USDT", 0.0) or 0.0)
            total_btc = float(balance.get("total", {}).get("BTC", 0.0) or 0.0)
            free_btc = float(balance.get("free", {}).get("BTC", 0.0) or 0.0)

            return {
                "success": True,
                "sandbox": self.sandbox,
                "mode": "TESTNET (SANDBOX)" if self.sandbox else "LIVE (REAL MONEY)",
                "total_usdt": total_usdt,
                "free_usdt": free_usdt,
                "total_btc": total_btc,
                "free_btc": free_btc,
                "symbol": self.symbol,
                "error": None,
            }
        except ccxt.AuthenticationError as e:
            logger.error("[LIVE BROKER] Authentication failed: %s", e)
            return {"success": False, "mode": "UNKNOWN", "error": f"AuthenticationError: {str(e)}"}
        except Exception as e:
            logger.error("[LIVE BROKER] Connection check failed: %s", e)
            return {"success": False, "mode": "UNKNOWN", "error": str(e)}

    def get_balance(self) -> Dict[str, float]:
        """Fetch current free and total balances."""
        try:
            bal = self.exchange.fetch_balance()
            return {
                "USDT": float(bal.get("free", {}).get("USDT", 0.0) or 0.0),
                "total_USDT": float(bal.get("total", {}).get("USDT", 0.0) or 0.0),
                "BTC": float(bal.get("free", {}).get("BTC", 0.0) or 0.0),
                "total_BTC": float(bal.get("total", {}).get("BTC", 0.0) or 0.0),
            }
        except Exception as e:
            logger.error("[LIVE BROKER] Error fetching balance: %s", e)
            return {"USDT": 0.0, "total_USDT": 0.0, "BTC": 0.0, "total_BTC": 0.0}

    def _round_step_size(self, qty: float) -> float:
        """Round quantity down to the exchange step_size."""
        self.load_markets()
        if self.step_size <= 0:
            return round(qty, 6)
        precision = max(0, int(round(-math.log10(self.step_size))))
        factor = 10 ** precision
        return math.floor(qty * factor) / factor

    def fill_buy(self, price: float, size_usd: float) -> float:
        """
        Execute a spot market BUY order on Binance.
        
        Args:
            price: current estimated market price
            size_usd: USD notional amount to purchase
            
        Returns:
            float: actual weighted average fill price from the exchange
        """
        self.load_markets()

        if size_usd < self.min_notional:
            msg = f"Order size ${size_usd:.2f} is below Binance minimum notional ${self.min_notional:.2f}"
            logger.error("[LIVE BROKER] %s", msg)
            raise ValueError(msg)

        # Check balance
        bal = self.get_balance()
        free_usdt = bal.get("USDT", 0.0)
        if free_usdt < size_usd:
            msg = f"Insufficient free USDT: requested ${size_usd:.2f}, available ${free_usdt:.2f}"
            logger.error("[LIVE BROKER] %s", msg)
            raise ccxt.InsufficientFunds(msg)

        # Compute quantity of BTC to buy
        estimated_qty = size_usd / price
        qty = self._round_step_size(estimated_qty)

        if qty < self.min_qty:
            msg = f"Calculated quantity {qty:.6f} below Binance min_qty {self.min_qty:.6f}"
            logger.error("[LIVE BROKER] %s", msg)
            raise ValueError(msg)

        logger.info("[LIVE BROKER] Submitting MARKET BUY for %s: qty=%.6f (notional ~$%.2f)",
                    self.symbol, qty, size_usd)

        try:
            order = self.exchange.create_market_buy_order(self.symbol, qty)
            logger.info("[LIVE BROKER] BUY order filled! Order ID: %s, status: %s",
                        order.get("id"), order.get("status"))

            # Extract actual fill price
            fill_price = float(order.get("average") or order.get("price") or price)
            return fill_price

        except Exception as e:
            logger.critical("[LIVE BROKER] LIVE BUY ORDER EXECUTION FAILED: %s", e)
            raise

    def fill_sell(self, price: float, qty: float) -> float:
        """
        Execute a spot market SELL order on Binance.

        Args:
            price: current estimated market price
            qty: BTC quantity to sell

        Returns:
            float: actual weighted average fill price from the exchange
        """
        self.load_markets()
        rounded_qty = self._round_step_size(qty)

        # Check free BTC balance
        bal = self.get_balance()
        free_btc = bal.get("BTC", 0.0)

        # Avoid dust or micro rounding discrepancies
        if rounded_qty > free_btc:
            rounded_qty = self._round_step_size(free_btc)

        if rounded_qty < self.min_qty:
            msg = f"Sell quantity {rounded_qty:.6f} is below Binance min_qty {self.min_qty:.6f}"
            logger.error("[LIVE BROKER] %s", msg)
            raise ValueError(msg)

        notional = rounded_qty * price
        if notional < self.min_notional:
            msg = f"Sell notional ${notional:.2f} is below Binance min notional ${self.min_notional:.2f}"
            logger.error("[LIVE BROKER] %s", msg)
            raise ValueError(msg)

        logger.info("[LIVE BROKER] Submitting MARKET SELL for %s: qty=%.6f (notional ~$%.2f)",
                    self.symbol, rounded_qty, notional)

        try:
            order = self.exchange.create_market_sell_order(self.symbol, rounded_qty)
            logger.info("[LIVE BROKER] SELL order filled! Order ID: %s, status: %s",
                        order.get("id"), order.get("status"))

            fill_price = float(order.get("average") or order.get("price") or price)
            return fill_price

        except Exception as e:
            logger.critical("[LIVE BROKER] LIVE SELL ORDER EXECUTION FAILED: %s", e)
            raise


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.getenv("EXCHANGE_API_KEY", "")
    api_secret = os.getenv("EXCHANGE_API_SECRET", "")
    sandbox = os.getenv("EXCHANGE_SANDBOX", "true").lower() == "true"

    print(f"Testing LiveBroker... (Sandbox={sandbox})")
    broker = LiveBroker(api_key=api_key, api_secret=api_secret, sandbox=sandbox)
    res = broker.verify_connection()
    print("Verification Result:", res)
    broker.load_markets()
    print(f"Markets loaded: min_notional=${broker.min_notional}, step_size={broker.step_size}")
