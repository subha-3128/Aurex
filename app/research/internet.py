"""
Internet Research Module — fetches real-time market context from free public endpoints.

Sources (all zero-cost, no API keys required):
  1. Fear & Greed Index   — alternative.me
  2. Binance Orderbook    — public Binance REST (no auth)
  3. CoinGecko            — free tier (no key)
  4. CryptoPanic News     — free tier headlines

Returns a structured dict safe to pass into every agent's decide() context.
"""
from __future__ import annotations

import logging
import time
from typing import Any

import requests

logger = logging.getLogger(__name__)

_TIMEOUT = 8  # seconds per request
_CACHE: dict = {}
_CACHE_TS: float = 0.0
_CACHE_TTL = 120  # re-fetch every 2 min max


def fetch_research(symbol: str = "BTC/USDT") -> dict[str, Any]:
    """
    Return the latest market research snapshot.
    Results are cached for 2 minutes to avoid hammering free APIs.
    """
    global _CACHE, _CACHE_TS
    if time.time() - _CACHE_TS < _CACHE_TTL and _CACHE:
        return _CACHE

    btc_symbol = "BTCUSDT"  # Binance spot format

    result: dict[str, Any] = {
        "timestamp": time.time(),
        "fear_greed": _fetch_fear_greed(),
        "orderbook":  _fetch_orderbook(btc_symbol),
        "coingecko":  _fetch_coingecko(),
        "news":       _fetch_news(),
    }

    _CACHE = result
    _CACHE_TS = time.time()
    return result


# ── Individual source fetchers ───────────────────────────────────────────────

def _fetch_fear_greed() -> dict[str, Any]:
    """Fear & Greed Index from alternative.me (free, no key)."""
    try:
        resp = requests.get(
            "https://api.alternative.me/fng/?limit=1",
            timeout=_TIMEOUT
        )
        data = resp.json()["data"][0]
        score = int(data["value"])
        label = data["value_classification"]
        # Normalize to [-1, +1] sentiment: <25 = extreme fear = contrarian buy signal
        if score <= 25:
            sentiment = 1.0   # extreme fear → contrarian bullish
        elif score <= 45:
            sentiment = 0.3   # fear → slight bullish lean
        elif score <= 55:
            sentiment = 0.0   # neutral
        elif score <= 75:
            sentiment = -0.3  # greed → slight bearish lean
        else:
            sentiment = -1.0  # extreme greed → contrarian bearish
        return {"score": score, "label": label, "sentiment": sentiment}
    except Exception as e:
        logger.warning("Fear & Greed fetch failed: %s", e)
        return {"score": 50, "label": "Neutral", "sentiment": 0.0}


def _fetch_orderbook(symbol: str = "BTCUSDT") -> dict[str, Any]:
    """
    Binance public orderbook — top 20 levels (no API key required).
    Computes bid/ask volume imbalance as a sentiment signal.
    """
    try:
        resp = requests.get(
            f"https://api.binance.com/api/v3/depth",
            params={"symbol": symbol, "limit": 20},
            timeout=_TIMEOUT
        )
        data = resp.json()
        bids = data.get("bids", [])
        asks = data.get("asks", [])
        bid_vol = sum(float(b[1]) for b in bids)
        ask_vol = sum(float(a[1]) for a in asks)
        total = bid_vol + ask_vol or 1.0
        imbalance = (bid_vol - ask_vol) / total  # +1 = all bids, -1 = all asks
        best_bid = float(bids[0][0]) if bids else 0.0
        best_ask = float(asks[0][0]) if asks else 0.0
        spread_pct = ((best_ask - best_bid) / best_bid * 100) if best_bid > 0 else 0.0
        return {
            "bid_volume": round(bid_vol, 4),
            "ask_volume": round(ask_vol, 4),
            "imbalance": round(imbalance, 4),   # > 0 = more buy pressure
            "best_bid": best_bid,
            "best_ask": best_ask,
            "spread_pct": round(spread_pct, 4),
        }
    except Exception as e:
        logger.warning("Orderbook fetch failed: %s", e)
        return {"bid_volume": 0, "ask_volume": 0, "imbalance": 0.0, "best_bid": 0.0, "best_ask": 0.0, "spread_pct": 0.0}


def _fetch_coingecko() -> dict[str, Any]:
    """CoinGecko free tier — BTC market data (no key)."""
    try:
        resp = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={
                "ids": "bitcoin",
                "vs_currencies": "usd",
                "include_market_cap": "true",
                "include_24hr_change": "true",
                "include_24hr_vol": "true",
            },
            timeout=_TIMEOUT,
            headers={"Accept": "application/json"}
        )
        btc = resp.json().get("bitcoin", {})
        change_24h = btc.get("usd_24h_change", 0.0) or 0.0
        # Normalized momentum: big positive change = bullish signal
        momentum = max(-1.0, min(1.0, change_24h / 10.0))
        return {
            "price_usd": btc.get("usd", 0.0),
            "market_cap": btc.get("usd_market_cap", 0.0),
            "volume_24h": btc.get("usd_24h_vol", 0.0),
            "change_24h_pct": round(change_24h, 4),
            "momentum": round(momentum, 4),
        }
    except Exception as e:
        logger.warning("CoinGecko fetch failed: %s", e)
        return {"price_usd": 0.0, "market_cap": 0.0, "volume_24h": 0.0, "change_24h_pct": 0.0, "momentum": 0.0}


def _fetch_news() -> dict[str, Any]:
    """
    Live crypto news headlines via Google News RSS (100% free, no key required).
    Returns headline list + bullish/bearish keyword sentiment analysis.
    """
    try:
        import xml.etree.ElementTree as ET
        resp = requests.get(
            "https://news.google.com/rss/search?q=bitcoin+crypto&hl=en-US&gl=US&ceid=US:en",
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"},
            timeout=_TIMEOUT
        )
        if resp.status_code != 200:
            return {"headlines": [], "bullish_count": 0, "bearish_count": 0, "news_sentiment": 0.0}

        root = ET.fromstring(resp.content)
        items = root.findall(".//item")[:8]
        headlines = []
        for item in items:
            title_el = item.find("title")
            if title_el is not None and title_el.text:
                # Remove source trailer if present (e.g., ' - CoinDesk')
                clean_title = title_el.text.rsplit(" - ", 1)[0].strip()
                headlines.append(clean_title)

        # Simple sentiment count
        bullish_words = {"surge", "bull", "rally", "high", "gain", "up", "rise", "buy", "breakout", "record", "pump", "ath", "jump", "soar"}
        bearish_words = {"crash", "bear", "drop", "low", "loss", "down", "fall", "sell", "dump", "fear", "decline", "slump", "tank"}
        bull_count = sum(any(w in h.lower() for w in bullish_words) for h in headlines)
        bear_count = sum(any(w in h.lower() for w in bearish_words) for h in headlines)
        total = bull_count + bear_count or 1
        news_sentiment = (bull_count - bear_count) / total
        return {
            "headlines": headlines,
            "bullish_count": bull_count,
            "bearish_count": bear_count,
            "news_sentiment": round(news_sentiment, 4),
        }
    except Exception as e:
        logger.warning("News fetch failed: %s", e)
        return {"headlines": [], "bullish_count": 0, "bearish_count": 0, "news_sentiment": 0.0}


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO)
    data = fetch_research()
    print(json.dumps(data, indent=2, default=str))
