"""
Database layer — SQLite with WAL mode.

Tables:
  candles      — OHLCV price history
  agent_trades — per-agent real trade execution log
  agent_ledger — persistent agent state (one row per agent, upserted)
"""
from __future__ import annotations

import logging
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DB_PATH = Path(os.getenv("DB_PATH", "data/trading.db"))


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn


@contextmanager
def get_conn():
    conn = _conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create all tables if they do not yet exist."""
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS candles (
                timestamp   INTEGER NOT NULL,
                symbol      TEXT    NOT NULL,
                timeframe   TEXT    NOT NULL,
                open        REAL    NOT NULL,
                high        REAL    NOT NULL,
                low         REAL    NOT NULL,
                close       REAL    NOT NULL,
                volume      REAL    NOT NULL,
                PRIMARY KEY (timestamp, symbol, timeframe)
            );

            CREATE TABLE IF NOT EXISTS agent_ledger (
                agent_id          TEXT PRIMARY KEY,
                name              TEXT    NOT NULL,
                description       TEXT,
                status            TEXT    NOT NULL DEFAULT 'ACTIVE',
                allocated_capital REAL    NOT NULL,
                cash              REAL    NOT NULL,
                reward_score      REAL    NOT NULL DEFAULT 0.0,
                trade_count       INTEGER NOT NULL DEFAULT 0,
                wins              INTEGER NOT NULL DEFAULT 0,
                losses            INTEGER NOT NULL DEFAULT 0,
                total_pnl         REAL    NOT NULL DEFAULT 0.0,
                max_drawdown_pct  REAL    NOT NULL DEFAULT 0.0,
                has_position      INTEGER NOT NULL DEFAULT 0,
                last_updated      INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS agent_trades (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp       INTEGER NOT NULL,
                agent_id        TEXT    NOT NULL,
                agent_name      TEXT,
                symbol          TEXT    NOT NULL,
                action          TEXT    NOT NULL,   -- BUY / SELL
                confidence      REAL,
                entry_price     REAL,
                exit_price      REAL,
                position_size   REAL,
                qty             REAL,
                gross_pnl       REAL,
                fees            REAL,
                net_pnl         REAL,
                reward_delta    REAL,
                new_reward_score REAL,
                regime          TEXT,
                rationale       TEXT,
                notes           TEXT
            );
        """)
    logger.info("Database initialised at %s", DB_PATH)


# ── Candle helpers ────────────────────────────────────────────────────────────

def upsert_candles(rows: list[dict], symbol: str, timeframe: str) -> int:
    if not rows:
        return 0
    with get_conn() as conn:
        conn.executemany(
            """INSERT OR REPLACE INTO candles
               (timestamp, symbol, timeframe, open, high, low, close, volume)
               VALUES (:timestamp, :symbol, :timeframe, :open, :high, :low, :close, :volume)""",
            [{**r, "symbol": symbol, "timeframe": timeframe} for r in rows],
        )
    return len(rows)


def load_candles(symbol: str, timeframe: str, limit: int | None = None) -> list[dict]:
    with get_conn() as conn:
        sql = "SELECT * FROM candles WHERE symbol=? AND timeframe=? ORDER BY timestamp ASC"
        if limit:
            sql += f" LIMIT {int(limit)}"
        rows = conn.execute(sql, (symbol, timeframe)).fetchall()
    return [dict(r) for r in rows]


def latest_candle_ts(symbol: str, timeframe: str) -> int | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT MAX(timestamp) as max_ts FROM candles WHERE symbol=? AND timeframe=?",
            (symbol, timeframe)
        ).fetchone()
        return row["max_ts"] if row and row["max_ts"] is not None else None


def load_as_dataframe(symbol: str, timeframe: str, limit: int | None = None):
    import pandas as pd
    rows = load_candles(symbol, timeframe, limit=limit)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    df.set_index("timestamp", inplace=True)
    return df


# ── Agent state helpers ───────────────────────────────────────────────────────

def save_agent_state(state: dict) -> None:
    """Upsert the agent state (one row per agent_id)."""
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO agent_ledger
               (agent_id, name, description, status, allocated_capital, cash,
                reward_score, trade_count, wins, losses, total_pnl, max_drawdown_pct,
                has_position, last_updated)
               VALUES (:agent_id, :name, :description, :status, :allocated_capital, :cash,
                       :reward_score, :trade_count, :wins, :losses, :total_pnl, :max_drawdown_pct,
                       :has_position, :last_updated)
               ON CONFLICT(agent_id) DO UPDATE SET
                 name=excluded.name,
                 description=excluded.description,
                 status=excluded.status,
                 allocated_capital=excluded.allocated_capital,
                 cash=excluded.cash,
                 reward_score=excluded.reward_score,
                 trade_count=excluded.trade_count,
                 wins=excluded.wins,
                 losses=excluded.losses,
                 total_pnl=excluded.total_pnl,
                 max_drawdown_pct=excluded.max_drawdown_pct,
                 has_position=excluded.has_position,
                 last_updated=excluded.last_updated
            """,
            {
                **state,
                "has_position": int(state.get("has_position", False)),
                "last_updated": int(__import__("time").time() * 1000),
            }
        )


def load_agent_states() -> list[dict]:
    """Load all agent states from the ledger."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM agent_ledger ORDER BY agent_id"
        ).fetchall()
    result = [dict(r) for r in rows]
    for r in result:
        r["has_position"] = bool(r.get("has_position", 0))
    return result


def insert_agent_trade(trade: dict) -> None:
    """Log a real executed trade linked to a specific agent."""
    with get_conn() as conn:
        cols = ", ".join(trade.keys())
        placeholders = ", ".join(f":{k}" for k in trade.keys())
        conn.execute(
            f"INSERT INTO agent_trades ({cols}) VALUES ({placeholders})", trade
        )


def get_agent_trades(agent_id: str | None = None, limit: int = 100) -> list[dict]:
    with get_conn() as conn:
        if agent_id:
            rows = conn.execute(
                "SELECT * FROM agent_trades WHERE agent_id=? ORDER BY timestamp DESC LIMIT ?",
                (agent_id, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM agent_trades ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            ).fetchall()
    return [dict(r) for r in rows]
