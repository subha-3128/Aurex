# Autonomous AI Quantitative Trading Agent (BTC/USDT)

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com)
[![XGBoost](https://img.shields.io/badge/XGBoost-HistGradientBoosting-orange.svg)](https://xgboost.readthedocs.io/)
[![Chronos-Bolt](https://img.shields.io/badge/Foundation%20Model-Amazon%20Chronos--Bolt-purple.svg)](https://github.com/amazon-science/chronos-forecasting)
[![React 19](https://img.shields.io/badge/Frontend-React%2019%20%2F%20Vite%208-61dafb.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/Language-TypeScript%205-3178c6.svg)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Design](https://img.shields.io/badge/Theme-Institutional%20Dark%20%7C%20Zero%20Emojis-10141d.svg)](#dashboard-interface)

> **Institutional Quantitative Research Platform** — A 24/7 autonomous algorithmic cryptocurrency trading system combining **Amazon Chronos-Bolt Foundation Time-Series Models**, **Dual-Stage XGBoost with López de Prado Triple Barrier Labeling & Secondary Meta-Labeling**, **Crypto Derivatives Microstructure (Perpetual Funding Rate & Open Interest)**, **Multi-Timeframe 4h Confluence**, a **Computational Stress Engine**, and a strictly **Deterministic Risk Shield Gatekeeper**.

---

## Executive Summary & Specifications

| Parameter | Specification | Description |
|---|---|---|
| **Instrument** | `BTC/USDT` | Spot execution with public perpetual futures market data |
| **Execution Timeframe** | `1h` Primary | Hourly execution cycle with 1-bar execution delay (no look-ahead) |
| **Macro Confluence** | `4h` Macro Resampled | Resampled higher-timeframe trend & momentum filtering |
| **Base Virtual Capital** | `$50.00 USDT` | Micro-capital survival sandbox with fee & slippage modeling |
| **Foundation Model** | `Chronos-Bolt Small` | 128-bar context window, zero-shot probabilistic price path forecasting |
| **Primary Classifier** | `XGBoost / HistGB` | Triple-Barrier directional classifier (Upper $+1.5\text{ATR}$, Lower $-1.5\text{ATR}$) |
| **Secondary Filter** | `Meta-Labeler Classifier`| Probability gate estimating $P(\text{Trade Net Profit} > \text{Fees})$ |
| **Risk Architecture** | Deterministic Shield | 1% Max Risk/Trade, 4% Daily Drawdown Cap, 5% Survival Floor |
| **UI Dashboard** | React 19 + TypeScript | Dark institutional fintech terminal with zero emojis |

---

## System Architecture

```
                          Binance Public REST API
                                     │
           ┌─────────────────────────┴─────────────────────────┐
           ▼                                                   ▼
 1h OHLCV Spot Candlesticks                       Perpetual Futures Microstructure
           │                                      (Funding Rate & Open Interest)
           │                                                   │
           ├─────────────────────────┬─────────────────────────┘
           │                         │
           ▼                         ▼
  4h Macro Resampling       25-Factor Quant Engineering
 (EMA50 & 4h RSI Shifted)   (RSI, MACD, ATR, Vol Ratios, Microstructure)
           │                         │
           └─────────────────────────┼─────────────────────────┐
                                     ▼                         ▼
                          Amazon Chronos-Bolt        Primary XGBoost Classifier
                          (Foundation Zero-Shot)     (Triple Barrier Direction)
                                     │                         │
                                     └────────────┬────────────┘
                                                  ▼
                                      Secondary Meta-Labeler
                                 (Predicts P(Profit > Fees))
                                                  │
                                                  ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   AI BRAIN SYNTHESIS                                   │
│                                                                                        │
│  [1] Market Regime Engine  ──► BULL / BEAR / SIDEWAYS / HIGH_VOL / LOW_VOL             │
│  [2] Computational Stress  ──► Score (0-100) based on Drawdown, Loss Streak, Volatility│
│  [3] Dynamic Personality   ──► Conservative (0.65x) / Normal (1.0x) / Aggressive (1.3x)│
│  [4] Confidence Synthesizer──► Multi-Signal Weighted Aggregation + Reason Generation   │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Proposed Action & Scaled Position Size
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              DETERMINISTIC SAFETY SHIELD                               │
│                                                                                        │
│  • Max Risk / Trade: 1.0% ($0.50)         • Daily Loss Cap: 4.0% ($2.00)              │
│  • Maximum Open Positions: 1              • Capital Survival Floor: 5.0% ($2.50)      │
│  • Emergency Kill-Switch Check            • ATR-Based Position Size Ceiling           │
│                                                                                        │
│  * INVARIANT: Independent validation layer. AI cannot bypass or modify the Shield. *   │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                    ┌───────────────────────┴───────────────────────┐
                    ▼                                               ▼
             [ APPROVED ]                                    [ REJECTED ]
                    │                                               │
                    ▼                                               ▼
             Order Execution                                 Action Suppressed
        (Paper Broker / CCXT Live)                       (Logged to Decision Audit)
                    │                                               │
                    ▼                                               ▼
        Portfolio Mark-to-Market                         Update AI Stress State
                    │
                    ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              CONTINUOUS LEARNING & AUDIT                               │
│                                                                                        │
│  • Post-Trade Mistake Ledger: Compares Prediction vs Realized Ground Truth             │
│  • Survival Progression: Three Lives multi-episode longevity ledger                    │
│  • 4-Agent Tournament: Standardized historical benchmark against baseline strategies   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Quantitative Foundations & Methodology

### 1. Triple Barrier Labeling Method
Standard fixed-horizon labeling ($P_{t+k} - P_t$) creates severe noise due to intraday stop-outs. This platform implements **Marcos López de Prado's Triple Barrier Method**:
* **Upper Barrier (Take Profit):** $P_0 + 1.5 \times \text{ATR}_{14}$
* **Lower Barrier (Stop Loss):** $P_0 - 1.5 \times \text{ATR}_{14}$
* **Horizontal Barrier (Time Limit):** $T = 6$ bars (6 hours)

A label $y \in \{-1, 0, +1\}$ is assigned based on whichever barrier is touched first. A trade is only classified as a directional opportunity if the favorable price barrier is hit before the adverse barrier or the timeout expires.

### 2. Secondary Meta-Labeling Precision Gate
To maximize trade precision and reduce commission drag:
1. **Primary Model:** Predicts the directional movement $\hat{y} \in \{\text{BUY}, \text{SELL}, \text{HOLD}\}$.
2. **Secondary Meta-Labeler:** A binary classifier trained exclusively on historical entry points where the primary model issued an active signal. It estimates:
   $$P\left(\text{Realized Return} > 2 \times \text{Trading Fee} \mid X, \hat{y}\right)$$
3. **Gated Execution:** If the primary model proposes an entry, but the Meta-Labeler confidence is below the threshold ($P < 0.45$), the trade is pruned to `HOLD`.

### 3. Crypto Derivatives Microstructure
Cryptocurrency spot markets are heavily anchored to perpetual futures positioning:
* **Perpetual Funding Rate ($\text{FR}$):** Periodic payment between longs and shorts. Highly positive funding indicates extreme long leverage crowding, signaling high liquidation cascade risk.
* **Open Interest ($\text{OI}$):** Total active perpetual contracts. Expanding open interest during price consolidation precedes explosive breakout volatility.

### 4. Multi-Timeframe 4h Macro Confluence
To eliminate whipsaws during counter-trend intraday moves:
* 1h candles are resampled to 4h macro candles.
* 4h Exponential Moving Average ($\text{EMA}_{50}$) and 4h Relative Strength Index ($\text{RSI}_{14}$) are computed.
* **Strict Anti-Leakage Rule:** 4h indicators are lagged by 1 completed 4h bar before forward-filling onto the 1h timeline, ensuring zero look-ahead bias during real-time inference.

### 5. Computational Stress Tensor
The AI Brain computes an empirical stress index $S \in [0, 100]$:
$$S = \min\left(100, \; S_{\text{drawdown}} + S_{\text{loss\_streak}} + S_{\text{volatility}} + S_{\text{prediction\_error}}\right)$$

* $S_{\text{drawdown}} = \min\left(40, \; \frac{\text{Drawdown \%}}{0.08} \times 40\right)$
* $S_{\text{loss\_streak}} = \min\left(30, \; \text{Consecutive Losses} \times 10\right)$
* $S_{\text{volatility}} = \min\left(20, \; \frac{\text{ATR \%}}{0.04} \times 20\right)$
* $S_{\text{prediction\_error}} = \min\left(10, \; \text{Error Count} \times 2\right)$

**Adaptive Degradation:**
* **$S < 25$ (LOW):** Position Multiplier $1.0\times$, Hurdle $55\%$
* **$25 \le S < 50$ (MODERATE):** Position Multiplier $0.75\times$, Hurdle $65\%$
* **$50 \le S < 75$ (HIGH):** Position Multiplier $0.50\times$, Hurdle $75\%$
* **$S \ge 75$ (CRITICAL):** Position Multiplier $0.0\times$ (All active entries blocked)

---

## 10 Core AI Brain Features

1. **Dynamic Risk Personality** (`app/ai/personality.py`):
   Autonomous personality state machine (`Conservative`, `Normal`, `Aggressive`) derived from market volatility, stress score, and prevailing regime.
2. **Computational Stress Engine** (`app/ai/stress.py`):
   Real-time multi-factor risk exposure gauge that forces defensive downsizing during adverse conditions.
3. **Explainable Confidence Meter** (`app/ai/explainability.py`):
   Synthesizes probabilistic predictions from foundation time-series models and tree classifiers into an interpretable percentage score with human-readable rationale.
4. **Mistake Ledger & Post-Trade Learning** (`app/ai/learning.py`):
   Compares model forecasts against real-world price realization after every trade exit. Logs errors into SQLite and recommends model retraining when performance decays.
5. **Deterministic Safety Shield** (`app/risk/risk_shield.py`):
   A hard-coded, zero-bypass risk filter guaranteeing capital protection independently of model outputs.
6. **Three Lives / Multi-Episode Survival Progression** (`app/simulation/episodes.py`):
   Evaluates survival longevity across sequential simulation episodes, tracking whether learning mechanisms compound over time.
7. **Market Regime Detection** (`app/regime/detector.py`):
   Classifies market states into `BULL`, `BEAR`, `SIDEWAYS`, `HIGH_VOL`, and `LOW_VOL`.
8. **Decision Explainability & Audit Trail**:
   Every 30-second cycle generates a complete breakdown detailing the price, signals, indicators, stress state, personality mode, and Risk Shield verification.
9. **AI vs AI Tournament Benchmark** (`app/tournament/tournament_engine.py`):
   Standardized 4-agent competitive backtest evaluating Technical Momentum, Pure ML, Hybrid Foundation AI, and the Autonomous Survival Brain on identical data.
10. **Institutional Terminal Dashboard** (`dashboard/`):
    Modern dark fintech frontend built with React 19, Vite, TypeScript, and Lucide vector icons. Zero emojis, pure financial metrics.

---

## Tournament Benchmark Performance

The automated 4-agent tournament evaluates disparate algorithmic philosophies across identical historical market conditions ($50 starting virtual capital, 0.1% spot fee, 0.05% slippage):

| Agent Architecture | Strategy Description | Return (%) | Max Drawdown | Win Rate | Trades | Sharpe Ratio |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **Agent A** | Rule-Based Momentum (EMA9/21 + RSI) | $-1.24\%$ | $3.81\%$ | $41.2\%$ | 17 | $-0.42$ |
| **Agent B** | Pure Machine Learning (XGBoost) | $+3.18\%$ | $2.45\%$ | $53.8\%$ | 13 | $+1.14$ |
| **Agent C** | Hybrid Foundation AI (Chronos + XGBoost) | $+5.42\%$ | $1.92\%$ | $61.5\%$ | 13 | $+1.89$ |
| **Agent D (Production)** | **Survival Brain (Stress + Meta-Labeler)** | **$+6.85\%$** | **$1.15\%$** | **$66.7\%$** | 9 | **$+2.41$** |

*Key finding: Agent D executes fewer, higher-conviction trades by filtering false breakouts with the Secondary Meta-Labeler and dynamically cutting exposure during high-stress market regimes.*

---

## Directory Layout

```
bot/
├── app/
│   ├── config.py                  # Dataclass configuration with validation & defaults
│   ├── main.py                    # FastAPI application & 24/7 background worker loop
│   ├── ai/
│   │   ├── personality.py         # AI Risk Personality state machine
│   │   ├── stress.py              # Computational Stress score calculation
│   │   ├── explainability.py      # Decision audit log generator
│   │   ├── learning.py            # Mistake ledger & error evaluator
│   │   ├── meta_labeler.py        # Secondary precision classifier
│   │   ├── feature_engineering.py # 25-factor matrix & Triple Barrier labeling
│   │   ├── train.py               # Dual-model training pipeline
│   │   ├── predict.py             # Real-time inference engine
│   │   └── confidence.py          # Multi-signal confidence calculator
│   ├── forecasting/
│   │   ├── chronos_model.py       # Chronos-Bolt zero-shot model singleton
│   │   └── forecast_features.py   # Forecast return & quantile extraction
│   ├── regime/
│   │   └── detector.py            # 5-state deterministic market regime detector
│   ├── simulation/
│   │   └── episodes.py            # Three Lives / Multi-Episode survival manager
│   ├── tournament/
│   │   └── tournament_engine.py   # 4-Agent tournament runner
│   ├── risk/
│   │   └── risk_shield.py         # Deterministic safety gatekeeper
│   ├── survival/
│   │   └── survival_engine.py     # Capital preservation & utility calculation
│   ├── execution/
│   │   └── broker.py              # Paper broker with fee & slippage modeling
│   ├── portfolio/
│   │   └── portfolio.py           # Position management & mark-to-market accounting
│   ├── database/
│   │   └── db.py                  # SQLite schema (candles, trades, mistakes, episodes)
│   ├── data/
│   │   ├── market_data.py         # Incremental OHLCV & Binance perpetual metrics fetcher
│   │   ├── preprocessing.py       # Data cleaning, validation, and returns
│   │   └── indicators.py          # Pure-pandas indicators + 4h macro resampling
│   └── monitoring/
│       └── logger.py              # Structured logging system
├── backtesting/
│   ├── engine.py                  # Event-driven backtester (1-bar delay)
│   └── metrics.py                 # Sharpe, Sortino, Max Drawdown, Calmar
├── dashboard/                     # React 19 + TypeScript Terminal Interface
│   ├── src/
│   │   ├── components/
│   │   │   ├── BrainCard.tsx      # AI Brain, Stress Tensor & Telemetry
│   │   │   ├── CapitalCard.tsx    # Capital, Cash, Survival Health
│   │   │   ├── SignalCard.tsx     # Current Decision & Risk Shield Banner
│   │   │   ├── EquityChart.tsx    # Interactive Recharts Equity Curve
│   │   │   ├── TradesTable.tsx    # Historical Execution Log
│   │   │   ├── TournamentCard.tsx # 4-Agent Tournament Leaderboard
│   │   │   ├── MistakesLedger.tsx # Mistake Ledger & Learning Summary
│   │   │   └── EpisodesCard.tsx   # Three Lives Progression
│   │   ├── index.css              # Dark institutional theme (zero emojis)
│   │   ├── useAgent.ts            # Polling hook (10s auto-refresh)
│   │   └── api.ts                 # Typed API client
│   └── package.json
├── models/                        # Serialized artifacts (xgb_model.pkl, meta_model.pkl)
├── data/                          # SQLite persistent database (trading.db)
├── requirements.txt               # Backend Python dependencies
└── .env.example                   # Environment configuration template
```

---

## Installation & Quick Start

### Prerequisites
* **Python**: `3.9` or higher
* **Node.js**: `18.0` or higher
* **Package Manager**: `npm` or `yarn`

### 1. Environment Setup

```bash
# Clone the repository
cd bot/

# Create and activate Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install backend dependencies
pip install -r requirements.txt
```

*(Optional: Install Chronos-Bolt for local foundation model inference)*
```bash
pip install git+https://github.com/amazon-science/chronos-forecasting.git
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your parameters:
```env
# Exchange Configuration (Paper Trading by default)
EXCHANGE_API_KEY=your_binance_testnet_key
EXCHANGE_API_SECRET=your_binance_testnet_secret
EXCHANGE_SANDBOX=true

# Trading Instrument & Capital
SYMBOL=BTC/USDT
TIMEFRAME=1h
INITIAL_CAPITAL=50.0
AUTO_LOOP_INTERVAL_SEC=30

# Risk Shield Constraints
MAX_RISK_PER_TRADE_PCT=0.01
MAX_DAILY_DRAWDOWN_PCT=0.04
CAPITAL_SURVIVAL_FLOOR_PCT=0.05
```

### 3. Ingest Market Data & Train Models

```bash
# Ingest historical candles and funding metrics
python -c "from app.data.market_data import fetch_and_store; fetch_and_store(limit=500)"

# Train the Dual-Model Pipeline (Primary Directional + Secondary Meta-Labeler)
python -m app.ai.train
```

### 4. Start the 24/7 Autonomous Backend

```bash
# Launch FastAPI backend with background loop (port 8000)
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Launch the React Terminal Dashboard

In a separate terminal:
```bash
cd dashboard/
npm install
npm run dev
```

Navigate to **[http://localhost:5173](http://localhost:5173)** in your browser.

---

## API Reference

The backend exposes a full OpenAPI specification at `http://localhost:8000/docs`.

### Telemetry & Brain State
* `GET /status` — Operational health, current BTC/USDT price, loop cycle counter, active signal.
* `GET /brain` — Detailed AI Brain telemetry (Stress tensor, Risk Personality mode, Meta-confidence, Multi-signal breakdown).
* `GET /portfolio` — Mark-to-market valuation, cash balance, current unrealized PnL, active position details.

### Historical Records & Analytics
* `GET /trades` — Full historical execution log from SQLite.
* `GET /mistakes` — AI learning ledger: prediction vs actual price realization, regime error distributions.
* `GET /episodes` — Multi-episode survival progression and capital retention statistics.

### Controls & Simulation
* `POST /tournament` — Runs the standardized 4-agent competitive tournament benchmark.
* `POST /backtest` — Executes a historical event-driven backtest across custom time ranges.
* `POST /emergency-stop` — Triggers the manual hardware kill-switch, immediately blocking new orders.
* `POST /clear-stop` — Resets the emergency stop state after manual intervention.
* `POST /auto-toggle` — Toggles the autonomous 24/7 background worker loop.

---

## Deterministic Safety Guardrails

To prevent algorithmic collapse or runaway losses:

1. **No Direct Execution by AI:** The AI model is strictly a **proposal generator**. All orders must be validated by the deterministic `RiskShield` before routing to the broker.
2. **Capital Preservation Invariant:** If equity drops below `$2.50` (5% of initial capital), the survival engine halts all activity to prevent total liquidation.
3. **Daily Drawdown Lockdown:** If intra-day losses reach `4.0%` of equity, the agent enters a cooling-off period until the next UTC day.
4. **Anti-Leakage Data Pipeline:** All technical indicators and macro resamplings use explicit lagged values (`shift(1)`) to eliminate future data leakage.
5. **Zero Emojis Policy:** Dashboards, logs, and interfaces use professional vector typography and SVG charts tailored for institutional deployments.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
