"""
Autonomous Multi-Agent AI Trading System — FastAPI backend.

4 AI agents each research the market independently, make their own
BUY/SELL/HOLD decisions, and trade real BTC/USDT through Binance.

Each agent has its own performance ledger:
  - Profitable trades earn reward points
  - Losing trades earn penalty points (2× magnitude)
  - Degraded agents (score < -50) get reduced capital and higher confidence hurdles
  - Dead agents (score < -100 or capital exhausted) are deactivated

Endpoints:
  GET  /status           — overall system health
  GET  /agents           — all 4 agent states with reward scores
  GET  /agents/{id}      — individual agent detail
  GET  /agents/{id}/trades — per-agent trade history
  GET  /research         — latest internet market research snapshot
  GET  /trades           — all trades across all agents
  GET  /broker/status    — live Binance account connection & balances
  POST /emergency-stop   — hard kill-switch
  POST /clear-stop       — reset emergency stop
  POST /auto-toggle      — toggle 24/7 loop on/off
"""
from __future__ import annotations

import asyncio
import logging
import math
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import cfg
from app.database.db import init_db, load_as_dataframe, insert_agent_trade, get_agent_trades
from app.data.market_data import fetch_and_store
from app.data.preprocessing import preprocess
from app.data.indicators import add_indicators
from app.regime.detector import detect_regime
from app.risk.risk_shield import RiskShield
from app.execution.live_broker import LiveBroker
from app.research.internet import fetch_research
from app.agents.lifecycle import AgentLifecycleManager
from app.monitoring.logger import setup_logging

setup_logging(cfg.log_level)
logger = logging.getLogger(__name__)

# ── Initialize Live Broker ────────────────────────────────────────────────────
try:
    broker = LiveBroker(
        api_key=cfg.api_key,
        api_secret=cfg.api_secret,
        sandbox=cfg.sandbox,
        symbol=cfg.symbol,
        max_allocated_capital=cfg.max_allocated_capital,
    )
    live_bal    = broker.get_balance()
    avail_usdt  = live_bal.get("USDT", 0.0)
    initial_cap = min(avail_usdt, cfg.max_allocated_capital) if avail_usdt > 0 else cfg.max_allocated_capital
    logger.info("[LIVE] Broker connected. Free USDT=$%.2f  Allocated cap=$%.2f", avail_usdt, initial_cap)
except Exception as e:
    logger.error("[LIVE] LiveBroker init failed: %s", e)
    raise RuntimeError(f"Cannot start without live broker: {e}")

# ── Initialize Agent Lifecycle ────────────────────────────────────────────────
lifecycle = AgentLifecycleManager(total_capital=initial_cap)
risk_shield = RiskShield(initial_cap)

_auto_running   = True
_cycle_count    = 0
_latest_state: dict = {}
_latest_research: dict = {}

LOOP_INTERVAL = cfg.auto_loop_interval_sec


# ── Core trading cycle ────────────────────────────────────────────────────────

def _run_cycle() -> dict:
    global _cycle_count, _latest_state, _latest_research

    # 1. Fetch market data
    try:
        raw_df = fetch_and_store(cfg.symbol, cfg.timeframe)
    except Exception as e:
        logger.error("Market data fetch failed: %s", e)
        return {"error": str(e)}

    if raw_df is None or raw_df.empty or len(raw_df) < 50:
        return {"error": "insufficient candle data"}

    df     = add_indicators(preprocess(raw_df), shift=True).dropna()
    row    = df.iloc[-1].to_dict()
    price  = float(row.get("close", 0.0))
    regime = detect_regime(row)

    # 2. Internet research (cached 2 min)
    try:
        research = fetch_research(cfg.symbol)
        _latest_research = research
    except Exception as e:
        logger.warning("Research fetch failed: %s", e)
        research = {}

    # 3. Build shared context for all agents
    context = {
        "indicators": row,
        "price":      price,
        "regime":     regime,
        "df":         df,
        "research":   research,
        "timestamp":  time.time(),
    }

    # 4. Run all agent decisions
    cycle_results = lifecycle.run_cycle(context)

    # 5. Route each agent's decision through Risk Shield → LiveBroker
    executed_trades = []
    for res in cycle_results:
        agent_id   = res.get("agent_id", "")
        action     = res.get("action", "HOLD")
        confidence = float(res.get("confidence", 0.0))

        agent = lifecycle.get_agent(agent_id)
        if not agent or not agent.can_trade():
            continue
        if action == "HOLD":
            continue

        # Confidence hurdle check per agent
        if confidence < agent.confidence_hurdle:
            logger.info("[%s] %s filtered: conf %.2f < hurdle %.2f",
                        agent_id, action, confidence, agent.confidence_hurdle)
            continue

        # Compute proposed size
        proposed_size = agent.cash * agent.size_multiplier

        # Risk Shield validation
        try:
            shield = risk_shield.check(action, confidence, agent.cash, float(row.get("atr_pct", 0.02) or 0.02))
        except Exception as e:
            logger.error("[RiskShield] %s", e)
            continue

        if not shield.allowed:
            logger.info("[%s] Risk Shield rejected %s: %s", agent_id, action, shield.reason)
            continue

        approved_size = min(proposed_size, shield.approved_size)

        # Execute via LiveBroker
        try:
            if action == "BUY" and not agent.has_position:
                fill = broker.fill_buy(price, approved_size)
                qty = (approved_size * (1 - float(cfg.taker_fee))) / fill
                lifecycle.record_position_open(agent_id, fill, approved_size, qty)
                insert_agent_trade({
                    "timestamp":    int(time.time() * 1000),
                    "agent_id":     agent_id,
                    "agent_name":   agent.name,
                    "symbol":       cfg.symbol,
                    "action":       "BUY",
                    "confidence":   confidence,
                    "entry_price":  fill,
                    "exit_price":   None,
                    "position_size": approved_size,
                    "qty":          qty,
                    "gross_pnl":    0.0,
                    "fees":         approved_size * cfg.taker_fee,
                    "net_pnl":      0.0,
                    "reward_delta": 0.0,
                    "new_reward_score": agent.reward_score,
                    "regime":       regime,
                    "rationale":    res.get("rationale", ""),
                    "notes":        f"LIVE BUY by {agent.name}",
                })
                executed_trades.append({"agent_id": agent_id, "action": "BUY", "size": approved_size, "price": fill})
                logger.info("[%s] LIVE BUY @ $%.2f  size=$%.2f  qty=%.6f", agent_id, fill, approved_size, qty)

            elif action == "SELL" and agent.has_position:
                qty = agent.position_qty
                if qty <= 0:
                    continue
                fill = broker.fill_sell(price, qty)
                proceeds   = qty * fill * (1 - float(cfg.taker_fee))
                gross_pnl  = qty * (fill - agent.position_entry)
                fees       = qty * fill * float(cfg.taker_fee)
                net_pnl    = proceeds - agent.position_size
                trade_size = agent.position_size

                lifecycle.record_position_close(agent_id, proceeds)
                lifecycle.apply_trade_outcome(agent_id, net_pnl, trade_size, agent.position_entry, fill)

                insert_agent_trade({
                    "timestamp":    int(time.time() * 1000),
                    "agent_id":     agent_id,
                    "agent_name":   agent.name,
                    "symbol":       cfg.symbol,
                    "action":       "SELL",
                    "confidence":   confidence,
                    "entry_price":  agent.position_entry if agent.position_entry else None,
                    "exit_price":   fill,
                    "position_size": trade_size,
                    "qty":          qty,
                    "gross_pnl":    round(gross_pnl, 6),
                    "fees":         round(fees, 6),
                    "net_pnl":      round(net_pnl, 6),
                    "reward_delta": round(agent.reward_score, 2),
                    "new_reward_score": round(agent.reward_score, 2),
                    "regime":       regime,
                    "rationale":    res.get("rationale", ""),
                    "notes":        f"LIVE SELL by {agent.name} | PnL=${net_pnl:.4f}",
                })
                executed_trades.append({"agent_id": agent_id, "action": "SELL", "pnl": net_pnl, "price": fill})
                logger.info("[%s] LIVE SELL @ $%.2f  pnl=$%.4f  new_score=%.2f  status=%s",
                            agent_id, fill, net_pnl, agent.reward_score, agent.status)

        except Exception as e:
            logger.error("[%s] Broker execution failed for %s: %s", agent_id, action, e)

    _cycle_count += 1
    _latest_state = {
        "price":           price,
        "regime":          regime,
        "symbol":          cfg.symbol,
        "timestamp":       time.time(),
        "cycle_count":     _cycle_count,
        "auto_running":    _auto_running,
        "agents":          lifecycle.all_to_dict(),
        "total_equity":    round(lifecycle.total_equity, 4),
        "executed_trades": executed_trades,
        "cycle_decisions": cycle_results,
    }
    return _latest_state


# ── Autonomous background loop ────────────────────────────────────────────────

async def _loop():
    global _auto_running
    logger.info("Autonomous trading loop started — interval=%ds", LOOP_INTERVAL)
    while _auto_running:
        try:
            _run_cycle()
        except Exception as e:
            logger.error("Cycle error: %s", e, exc_info=True)
        await asyncio.sleep(LOOP_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    task = asyncio.create_task(_loop())
    yield
    global _auto_running
    _auto_running = False
    task.cancel()


app = FastAPI(
    title="Autonomous Multi-Agent AI Trading System",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/status")
def status() -> dict:
    ver = broker.verify_connection()
    return {
        "status":               "alive",
        "broker_mode":          "LIVE (REAL MONEY)" if not cfg.sandbox else "TESTNET",
        "live_trading_enabled": cfg.live_trading_enabled,
        "auto_running":         _auto_running,
        "cycle_count":          _cycle_count,
        "total_equity":         round(lifecycle.total_equity, 4),
        "active_agents":        len(lifecycle.active_agents),
        "exchange_free_usdt":   ver.get("free_usdt", 0.0),
        "exchange_free_btc":    ver.get("free_btc", 0.0),
        "symbol":               cfg.symbol,
        "latest_price":         _latest_state.get("price", 0.0),
        "regime":               _latest_state.get("regime", "UNKNOWN"),
    }


@app.get("/agents")
def get_agents() -> list:
    return lifecycle.all_to_dict()


@app.get("/agents/{agent_id}")
def get_agent(agent_id: str) -> dict:
    agent = lifecycle.get_agent(agent_id)
    if not agent:
        raise HTTPException(404, f"Agent '{agent_id}' not found")
    return agent.to_dict()


@app.get("/agents/{agent_id}/trades")
def get_agent_trade_history(agent_id: str, limit: int = 50) -> list:
    agent = lifecycle.get_agent(agent_id)
    if not agent:
        raise HTTPException(404, f"Agent '{agent_id}' not found")
    return get_agent_trades(agent_id=agent_id, limit=limit)


@app.get("/trades")
def all_trades(limit: int = 100) -> list:
    return get_agent_trades(limit=limit)


@app.get("/research")
def market_research() -> dict:
    return _latest_research or fetch_research(cfg.symbol)


@app.get("/broker/status")
def broker_status() -> dict:
    ver = broker.verify_connection()
    return {
        "mode":                  "LIVE (REAL MONEY)" if not cfg.sandbox else "TESTNET",
        "sandbox":               cfg.sandbox,
        "success":               ver.get("success", False),
        "free_usdt":             ver.get("free_usdt", 0.0),
        "total_usdt":            ver.get("total_usdt", 0.0),
        "free_btc":              ver.get("free_btc", 0.0),
        "total_btc":             ver.get("total_btc", 0.0),
        "max_allocated_capital": cfg.max_allocated_capital,
        "min_notional":          broker.min_notional,
        "error":                 ver.get("error"),
    }


@app.get("/cycle")
def latest_cycle() -> dict:
    return _latest_state or {"status": "initializing"}


@app.post("/emergency-stop")
def emergency_stop() -> dict:
    from pathlib import Path
    Path("EMERGENCY_STOP").touch()
    global _auto_running
    _auto_running = False
    return {"stopped": True}


@app.post("/clear-stop")
def clear_stop() -> dict:
    from pathlib import Path
    p = Path("EMERGENCY_STOP")
    if p.exists():
        p.unlink()
    global _auto_running
    _auto_running = True
    return {"cleared": True}


@app.post("/auto-toggle")
def toggle_loop() -> dict:
    global _auto_running
    _auto_running = not _auto_running
    return {"auto_running": _auto_running}
