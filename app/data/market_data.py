"""
Market data fetcher — BTC/USDT OHLCV from Binance public REST.

Strategy (Ponytail): direct requests to Binance /klines endpoint,
no ccxt needed for historical data (no API key required).
Falls back to ccxt if EXCHANGE_USE_CCXT=true is set.

Incremental: only fetches candles newer than the latest stored timestamp.
"""
from __future__ import annotations
import os
import time
import logging
from datetime import datetime, timezone

import requests
import pandas as pd

from app.database.db import init_db, upsert_candles, load_candles, latest_candle_ts

logger = logging.getLogger(__name__)

SYMBOL = os.getenv("SYMBOL", "BTC/USDT")
TIMEFRAME = os.getenv("TIMEFRAME", "1h")
INITIAL_FETCH_BARS = int(os.getenv("INITIAL_FETCH_BARS", "2000"))

# Binance symbol format: BTCUSDT
_BINANCE_SYMBOL = SYMBOL.replace("/", "")

# Map timeframe string → Binance interval string
_TF_MAP = {
    "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
    "1h": "1h", "4h": "4h", "1d": "1d",
}

BINANCE_BASE = "https://api.binance.com"


def _binance_klines(
    symbol: str,
    interval: str,
    start_ms: int | None = None,
    limit: int = 1000,
) -> list[list]:
    """
    Fetch raw klines from Binance public endpoint.
    Returns list of [openTime, open, high, low, close, volume, ...].
    """
    params: dict = {"symbol": symbol, "interval": interval, "limit": limit}
    if start_ms is not None:
        params["startTime"] = start_ms

    url = f"{BINANCE_BASE}/api/v3/klines"
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _klines_to_dicts(raw: list[list]) -> list[dict]:
    return [
        {
            "timestamp": int(row[0]),   # milliseconds UTC
            "open":   float(row[1]),
            "high":   float(row[2]),
            "low":    float(row[3]),
            "close":  float(row[4]),
            "volume": float(row[5]),
        }
        for row in raw
    ]


def fetch_and_store(
    symbol: str = SYMBOL,
    timeframe: str = TIMEFRAME,
    limit: int = INITIAL_FETCH_BARS,
) -> pd.DataFrame:
    """
    Fetch OHLCV data from Binance, store incrementally in SQLite,
    return full DataFrame sorted by timestamp.

    On first run: fetches `limit` candles.
    On subsequent runs: only fetches candles after the latest stored timestamp.
    """
    init_db()
    interval = _TF_MAP.get(timeframe, "1h")
    binance_sym = symbol.replace("/", "")

    latest_ts = latest_candle_ts(symbol, timeframe)

    if latest_ts is None:
        logger.info("First run — fetching %d candles of %s %s", limit, symbol, timeframe)
        all_rows: list[dict] = []
        # Binance max per request = 1000; page backwards
        end_ms = None
        remaining = limit
        while remaining > 0:
            batch_limit = min(1000, remaining)
            params: dict = {
                "symbol": binance_sym,
                "interval": interval,
                "limit": batch_limit,
            }
            if end_ms is not None:
                params["endTime"] = end_ms - 1

            url = f"{BINANCE_BASE}/api/v3/klines"
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            batch = resp.json()
            if not batch:
                break
            rows = _klines_to_dicts(batch)
            all_rows = rows + all_rows           # prepend older candles
            end_ms = rows[0]["timestamp"]        # oldest in this batch
            remaining -= len(rows)
            if len(rows) < batch_limit:
                break
            time.sleep(0.1)                      # be nice to the API

        written = upsert_candles(all_rows, symbol, timeframe)
        logger.info("Stored %d candles", written)
    else:
        # Incremental fetch: only candles after latest stored
        start_ms = latest_ts + 1   # exclusive of last stored
        logger.info(
            "Incremental fetch from %s",
            datetime.fromtimestamp(start_ms / 1000, tz=timezone.utc),
        )
        all_rows = []
        while True:
            raw = _binance_klines(binance_sym, interval, start_ms=start_ms, limit=1000)
            if not raw:
                break
            rows = _klines_to_dicts(raw)
            # Skip the currently-open (incomplete) candle — it's the last one
            # Binance returns the current unclosed candle at the end
            if rows:
                rows = rows[:-1]
            all_rows.extend(rows)
            if len(raw) < 1000:
                break
            start_ms = rows[-1]["timestamp"] + 1
            time.sleep(0.1)

        if all_rows:
            written = upsert_candles(all_rows, symbol, timeframe)
            logger.info("Stored %d new candles", written)
        else:
            logger.info("No new candles")

    # Return full DataFrame
    return load_as_dataframe(symbol, timeframe)


def load_as_dataframe(symbol: str = SYMBOL, timeframe: str = TIMEFRAME) -> pd.DataFrame:
    """Load all stored candles as a DataFrame with DatetimeIndex."""
    rows = load_candles(symbol, timeframe)
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    df = df.set_index("timestamp").drop(columns=["symbol", "timeframe"], errors="ignore")
    df = df[["open", "high", "low", "close", "volume"]]
    df = df.sort_index()
    return df


# ── Derivatives & Microstructure (Public Binance Futures) ──────────────────────

BINANCE_FUTURES_BASE = "https://fapi.binance.com"
_cached_derivatives = {"funding_rate": 0.0001, "open_interest": 0.0, "open_interest_delta": 0.0}

def fetch_derivatives_metrics(symbol: str = SYMBOL) -> dict:
    """
    Fetch public perpetual futures funding rate and open interest from Binance.
    No API keys required. Fallbacks to cached/neutral values on failure.
    """
    global _cached_derivatives
    f_sym = symbol.replace("/", "").upper()
    result = dict(_cached_derivatives)

    # 1. Funding rate
    try:
        url_fr = f"{BINANCE_FUTURES_BASE}/fapi/v1/fundingRate"
        resp = requests.get(url_fr, params={"symbol": f_sym, "limit": 1}, timeout=5)
        if resp.ok:
            data = resp.json()
            if data and isinstance(data, list):
                result["funding_rate"] = float(data[0].get("fundingRate", 0.0001))
    except Exception as e:
        logger.debug("Could not fetch funding rate (%s); using fallback", e)

    # 2. Open interest
    try:
        url_oi = f"{BINANCE_FUTURES_BASE}/fapi/v1/openInterest"
        resp = requests.get(url_oi, params={"symbol": f_sym}, timeout=5)
        if resp.ok:
            data = resp.json()
            curr_oi = float(data.get("openInterest", 0.0))
            old_oi = _cached_derivatives.get("open_interest", curr_oi)
            result["open_interest"] = curr_oi
            result["open_interest_delta"] = ((curr_oi - old_oi) / old_oi) if old_oi > 0 else 0.0
    except Exception as e:
        logger.debug("Could not fetch open interest (%s); using fallback", e)

    _cached_derivatives = result
    return result

