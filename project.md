# Aurex — Autonomous AI Cryptocurrency Trading Engine — End-to-End Project Specification

## 1. Project Overview

### Proposed title

**Autonomous AI-Based Cryptocurrency Trading Agent with Survival-Driven Risk Management**

### Short description

This project develops a locally deployed autonomous AI trading system for **BTC/USDT spot trading**. The system receives market data, generates time-series forecasts using a pretrained forecasting model such as **Chronos-2**, combines those forecasts with technical and market features, and uses a machine-learning decision model such as **XGBoost** to produce BUY, SELL, or HOLD signals.

A separate deterministic **Risk Shield** controls whether a proposed trade is allowed. The trading agent can operate without asking the user for approval before every trade, while predefined safety limits prevent unrestricted risk-taking.

The project also introduces a **survival-based agent objective**. In simulation, the agent starts with a fixed virtual capital of **$50**. Profitable and disciplined behavior is rewarded, while losses and excessive drawdown are penalized. If simulated capital reaches zero, the episode terminates and the agent is considered to have "died" for that episode. This is a computational game mechanic, not literal harm to an AI.

The central research question is:

> **Can a survival-oriented objective combined with forecasting and hard risk controls improve capital preservation while maintaining useful trading performance?**

---

# 2. Problem Statement

Traditional beginner trading bots often follow simple rules such as:

- Buy when a moving average crosses another moving average.
- Sell when RSI becomes overbought.
- Buy after a fixed percentage drop.
- Use a single ML model to predict the next price.

These approaches have several limitations:

1. Cryptocurrency markets are noisy and non-stationary.
2. A price forecast alone does not tell the system whether a trade is economically worthwhile.
3. Transaction fees, spread, slippage, and execution delay can turn a theoretically profitable strategy into a losing strategy.
4. A model can produce a confident but incorrect prediction.
5. Optimizing only for return can encourage excessive risk.
6. Backtests can look excellent because of overfitting or data leakage.
7. A fully autonomous system needs a safety layer independent from the AI model.

Therefore, this project separates the system into specialized components:

**Forecasting → Decision Model → Risk Shield → Execution → Monitoring → Learning**

---

# 3. Main Objectives

## Primary objectives

1. Build a locally running autonomous BTC/USDT trading system.
2. Collect and process historical and live market data.
3. Generate probabilistic or point forecasts using a pretrained time-series model.
4. Extract technical and market features.
5. Use a machine-learning model to classify trading opportunities.
6. Implement BUY, SELL, and HOLD decisions.
7. Implement deterministic risk management.
8. Simulate a survival-based trading objective.
9. Backtest the complete strategy using unseen historical data.
10. Evaluate the system using financial and risk metrics.
11. Paper trade before any real-money deployment.
12. Provide a dashboard showing decisions, capital, risk, forecasts, and trade history.

## Secondary objectives

- Detect different market regimes.
- Estimate model confidence.
- Record prediction mistakes.
- Analyze why trades succeeded or failed.
- Compare different trading agents.
- Make every trade explainable.
- Keep the system modular and locally deployable.

---

# 4. Important Design Principle

The AI should **not directly control the exchange without constraints**.

The architecture should follow:

```text
AI proposes a trade
        ↓
Risk Shield checks the proposal
        ↓
If allowed → Execution Engine
        ↓
Exchange API
```

The AI cannot override the Risk Shield.

This is one of the most important safety and engineering principles of the project.

---

# 5. Why Cryptocurrency?

The first implementation targets cryptocurrency rather than stocks or forex.

Reasons:

- BTC/USDT can trade continuously.
- Historical OHLCV data is widely available.
- Exchange APIs support automated execution.
- The system can be tested with small nominal capital.
- Cryptocurrency provides many market regimes and volatile conditions for research.
- The project is technically convenient for a locally deployed autonomous agent.

The first version should use **BTC/USDT spot**, without leverage.

---

# 6. Why BTC/USDT?

BTC/USDT is a practical first market because:

- BTC has high market activity compared with many smaller crypto assets.
- USDT provides a simple quote currency.
- It is widely supported by cryptocurrency exchanges.
- There is substantial historical data for backtesting.
- It avoids the additional complexity of trading many assets simultaneously.

The system can later be extended to ETH/USDT or a multi-asset portfolio.

---

# 7. Core System Architecture

```text
                         BTC/USDT MARKET
                                │
                                ▼
                    ┌─────────────────────┐
                    │ Market Data Engine  │
                    │ OHLCV / Trades     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Data Processing     │
                    │ Cleaning / Resample │
                    └──────────┬──────────┘
                               │
                  ┌────────────┴────────────┐
                  ▼                         ▼
       ┌────────────────────┐    ┌────────────────────┐
       │ Technical Features │    │ Chronos-2 Forecast │
       │ RSI / EMA / MACD   │    │ Time-Series Model  │
       │ ATR / Volume / Vol │    └──────────┬─────────┘
       └──────────┬─────────┘               │
                  └────────────┬────────────┘
                               ▼
                    ┌─────────────────────┐
                    │ Feature Fusion      │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │ XGBoost Decision    │
                    │ BUY / SELL / HOLD   │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │ Confidence Layer   │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │ Market Regime       │
                    │ Detector             │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │  SURVIVAL ENGINE    │
                    │ Capital / Drawdown  │
                    │ Reward / Penalty    │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │     RISK SHIELD     │
                    │ Position / Loss /   │
                    │ Exposure / Limits   │
                    └──────────┬──────────┘
                               │
                     ┌─────────┴─────────┐
                     │                   │
                  REJECT              ALLOW
                     │                   │
                     ▼                   ▼
                  LOG ONLY       ┌──────────────┐
                                 │ Order Engine │
                                 └──────┬───────┘
                                        ▼
                                 Exchange API
                                        │
                                        ▼
                                     TRADE
                                        │
                         ┌──────────────┴──────────────┐
                         ▼                             ▼
                   Portfolio Update               Trade Log
                         │                             │
                         └──────────────┬──────────────┘
                                        ▼
                                Learning / Analysis
```

---

# 8. End-to-End Workflow

## Step 1 — Market Data Collection

The system receives BTC/USDT market data.

Initial implementation:

- 1-hour candles

Each candle contains:

- Open
- High
- Low
- Close
- Volume

This is called **OHLCV**.

For example:

```text
Timestamp
Open
High
Low
Close
Volume
```

The system should store historical data locally so that repeated experiments do not depend entirely on downloading the same data again.

---

# 9. Step 2 — Data Preprocessing

Raw data must be cleaned before entering the models.

Operations include:

- Sort by timestamp.
- Remove duplicates.
- Detect missing candles.
- Handle invalid values.
- Resample if required.
- Calculate returns.
- Normalize or transform selected features where appropriate.
- Ensure chronological ordering.

Most importantly:

> Future information must never enter the training features for a historical prediction.

This prevents **look-ahead bias/data leakage**.

---

# 10. Step 3 — Feature Engineering

The system creates market features.

## Price features

- Return
- Log return
- Price change
- Rolling return

## Trend features

- EMA
- SMA
- EMA difference

## Momentum features

- RSI
- MACD

## Volatility features

- ATR
- Rolling standard deviation
- Volatility regime

## Volume features

- Volume change
- Volume moving average
- Relative volume

## Market-state features

- Recent drawdown
- Recent volatility
- Trend direction
- Consecutive gains/losses

---

# 11. Step 4 — Chronos-2 Forecasting Layer

Chronos-2 is used as a **forecasting component**, not as the final trader.

The model receives historical time-series information and produces forecasts.

Conceptually:

```text
Past BTC/USDT data
        ↓
    Chronos-2
        ↓
Future price/series forecast
        ↓
Forecast-derived features
```

Useful features can include:

- Forecasted price
- Forecasted return
- Forecast direction
- Distance between forecast and current price
- Forecast uncertainty, when available

Example:

```text
Current price:      100,000
Forecast:           101,200

Expected move:      +1.20%
Forecast direction: Bullish
```

The exact forecast horizon should be defined before training and kept consistent during evaluation.

---

# 12. Important Point About Chronos-2

Chronos-2 is not a Bitcoin-specific "buy/sell brain."

It is a general time-series forecasting model.

Therefore:

```text
Chronos-2
    ≠
Trading Strategy
```

Instead:

```text
Chronos-2 forecast
       +
Technical indicators
       +
Market features
       ↓
XGBoost
       ↓
Trading decision
```

This hybrid design is more appropriate for the project than blindly converting a forecast into a trade.

---

# 13. Step 5 — Trading Decision Model

XGBoost can act as the decision layer.

Inputs may include:

```text
RSI
EMA
MACD
ATR
Volume
Recent returns
Volatility
Chronos forecast
Forecast return
Forecast direction
Market regime
```

Output:

```text
BUY
SELL
HOLD
```

The model can also output probabilities.

Example:

```text
BUY probability  = 0.84
SELL probability = 0.09
HOLD probability = 0.07
```

The system can interpret this as:

```text
Decision: BUY
Confidence: 84%
```

A confidence score should not be treated as a guarantee of correctness.

---

# 14. Step 6 — Target Variable

The model should not simply be trained to predict the exact future BTC price.

A better first formulation is a classification target based on future return.

Example:

```text
Future return over selected horizon > cost-adjusted threshold
        → BUY

Future return below negative threshold
        → SELL

Otherwise
        → HOLD
```

The threshold must account for expected trading costs.

This prevents the model from learning that a tiny theoretical price movement is worth trading when fees and slippage would consume the opportunity.

---

# 15. Step 7 — Market Regime Detection

The market is not always behaving in the same way.

A regime detector can classify the current state as:

```text
BULL TREND
BEAR TREND
SIDEWAYS
HIGH VOLATILITY
LOW VOLATILITY
```

Possible inputs:

- Trend strength
- Volatility
- Returns
- Moving-average relationships
- Volume

The trading system can use the regime as an additional feature.

For example:

```text
Market regime = HIGH VOLATILITY

→ Require stronger signal
→ Reduce position size
→ Increase caution
```

---

# 16. Step 8 — AI Confidence Layer

The system combines model information into a decision confidence.

Example:

```text
Chronos:          Bullish
XGBoost BUY:      86%
EMA trend:        Bullish
Volume:           Strong
Volatility:       Medium

Final signal:     BUY
Confidence:       82%
```

The exact confidence formula should be defined mathematically and tested rather than chosen only because it looks good.

---

# 17. Step 9 — Survival Engine

This is the unique research component.

The agent begins a simulated episode with:

```text
Initial capital = $50
```

The objective is not simply:

> Make as much money as possible.

Instead:

> Seek positive returns while preserving capital and avoiding catastrophic drawdown.

---

# 18. Survival State

The agent maintains variables such as:

```text
Capital
Equity
Drawdown
Profit/Loss
Loss streak
Number of trades
Exposure
Volatility
Prediction accuracy
```

Example:

```text
Initial capital: $50.00
Current equity:  $47.80
Drawdown:        -4.40%
Loss streak:     2
```

---

# 19. Survival Reward Concept

A conceptual reward function can combine:

```text
Reward =
Profit Reward
- Drawdown Penalty
- Transaction Cost Penalty
- Excessive Risk Penalty
- Large Loss Penalty
```

For example:

```text
R = α(Return)
    - β(Drawdown)
    - γ(Cost)
    - δ(Risk)
```

The coefficients α, β, γ and δ must be selected experimentally.

The purpose is to prevent the agent from maximizing return by taking uncontrolled risks.

---

# 20. Agent "Death"

The survival mechanic is implemented only as a computational state.

```text
Capital > 0
    ↓
Agent Alive
    ↓
Continue Episode

Capital ≤ 0
    ↓
Episode Terminated
    ↓
Agent "Dead"
```

A stronger implementation can terminate the episode before actual zero using a predefined catastrophic-loss threshold.

The important idea is:

> **The agent should learn that survival is necessary for future opportunities.**

It should not be programmed to gamble aggressively just because it is losing.

---

# 21. Adaptive Risk Behavior

The system can reduce risk when conditions deteriorate.

Example:

```text
Normal state
→ Normal position size

Moderate drawdown
→ Smaller position

Large drawdown
→ Very small position

Extreme volatility
→ Require higher confidence

Daily loss limit reached
→ Stop opening new positions
```

This creates a feedback loop:

```text
Trading result
      ↓
Portfolio state
      ↓
Risk state
      ↓
Position sizing / trade permission
      ↓
Next trade
```

---

# 22. Step 10 — Risk Shield

The Risk Shield is deterministic and should operate independently of the AI.

Possible controls:

- Maximum position size
- Maximum loss per trade
- Maximum daily loss
- Maximum total exposure
- Maximum number of open positions
- Maximum consecutive losses
- Minimum account reserve
- Volatility restriction
- API failure protection
- Emergency stop

Example configuration for research:

```text
Initial capital:          $50
Max risk per trade:       1%
Max daily loss:           4%
Max open positions:       1
Leverage:                 None
```

These are example research settings, not guaranteed optimal values.

---

# 23. Why No Leverage Initially?

Leverage increases both potential gains and losses.

For a $50 research system, leverage can make:

- risk management harder
- liquidation possible
- backtesting more complex
- execution errors more costly

Therefore the first implementation should use **spot trading without leverage**.

---

# 24. Step 11 — Position Sizing

The system should calculate position size instead of allowing the AI to choose arbitrary amounts.

A simplified concept:

```text
Allowed risk
-------------
Risk per unit

= Position size
```

For example, if the system decides the maximum acceptable loss is $0.50 and the stop distance implies $0.05 risk per unit:

```text
Position size = $0.50 / $0.05
              = 10 units
```

The actual implementation must also consider:

- exchange minimum order size
- lot/quantity precision
- available balance
- fees
- slippage

---

# 25. Step 12 — Trade Execution

Only after the Risk Shield approves a trade does the Order Engine communicate with the exchange API.

```text
Signal
  ↓
Risk validation
  ↓
Order construction
  ↓
Exchange API
  ↓
Order acknowledgement
  ↓
Fill status
  ↓
Portfolio update
```

The system must handle:

- API errors
- rejected orders
- partial fills
- network failures
- delayed responses
- duplicate order prevention

---

# 26. Step 13 — Trade Logging

Every decision should be recorded.

Example:

```text
Trade ID: 184
Timestamp: 2026-09-16 10:00
Symbol: BTC/USDT

Signal: BUY
Confidence: 0.84

Chronos forecast: Bullish
RSI: 58
EMA trend: Bullish
Volatility: Medium

Requested position: $8.50
Approved position: $8.00

Entry price: 100000
Exit price: 101200

Gross P/L: +$0.096
Fees: $0.016
Net P/L: +$0.080

Result: PROFIT
```

This makes the system auditable.

---

# 27. Step 14 — Learning From Mistakes

After a trade closes, compare:

```text
Predicted movement
        vs
Actual movement
```

Example:

```text
Predicted: +1.20%
Actual:    -0.80%

Prediction error: -2.00%
```

Store:

- prediction
- actual return
- market regime
- volatility
- indicators
- confidence
- result

Later, the dataset can be used to investigate systematic errors and periodically retrain the decision model.

Retraining should be controlled and versioned. The live system should never allow unrestricted self-modification of its own safety rules.

---

# 28. Step 15 — Backtesting

Backtesting is mandatory before live trading.

A correct process is:

```text
Historical Data
      ↓
Train Set
      ↓
Validation Set
      ↓
Unseen Test Set
      ↓
Walk-Forward Evaluation
      ↓
Performance Metrics
```

The system must include realistic:

- Trading fees
- Spread
- Slippage
- Execution delay
- Position constraints

---

# 29. Walk-Forward Testing

Instead of training once on the entire historical dataset, use chronological windows.

Conceptually:

```text
Train → Validate → Test
         ↓
Move window forward
         ↓
Train → Validate → Test
         ↓
Move window forward
```

This better represents how a live system would encounter new market data.

---

# 30. Data Leakage

Data leakage is one of the biggest threats to this project.

Bad example:

```text
Using tomorrow's price
to create today's feature
```

This creates an unrealistic backtest.

Correct principle:

> At time t, the model may only use information that would actually have been available at time t.

---

# 31. Evaluation Metrics

Do not evaluate the project using profit alone.

Measure:

### Return

Total percentage change in capital.

### Win Rate

```text
Winning trades
---------------- × 100
Total trades
```

### Maximum Drawdown

Largest peak-to-trough decline in portfolio value.

### Profit Factor

```text
Gross profit
------------
Gross loss
```

### Sharpe Ratio

A risk-adjusted return measure.

### Number of Trades

Important for understanding whether results depend on a few trades.

### Survival Duration

How long the simulated agent remains above the termination threshold.

### Transaction Costs

Total fees and estimated slippage.

---

# 32. Important Insight About Win Rate

A 70% win rate does not automatically mean the system is profitable.

Example:

```text
7 winning trades × $1   = +$7
3 losing trades × $3    = -$9

Net = -$2
```

Therefore the project should evaluate the complete distribution of returns and costs.

Similarly, a strategy can have fewer than 50% winning trades and still be profitable if its winning trades are sufficiently larger than its losses.

---

# 33. AI vs AI Experiment

A strong research extension is to create multiple agents using the same market data.

```text
Agent A
Technical-rule strategy

Agent B
XGBoost only

Agent C
Chronos + XGBoost

Agent D
Chronos + XGBoost + Survival Risk
```

All agents receive:

```text
Same starting capital
Same historical period
Same transaction-cost assumptions
Same evaluation rules
```

Then compare their metrics without changing the experimental conditions.

This allows you to study which architectural components contribute to performance and capital preservation.

---

# 34. Explainable Trading Dashboard

The dashboard should display:

```text
┌─────────────────────────────────────────┐
│         AUTONOMOUS TRADING AGENT        │
├─────────────────────────────────────────┤
│ Capital: $48.72                         │
│ P/L:     -$1.28                         │
│ Drawdown: 2.56%                         │
│ Status: 🟢 ACTIVE                       │
├─────────────────────────────────────────┤
│ BTC/USDT                                │
│ Current Price: $100,000                 │
│ Market Regime: BULL TREND               │
│ Chronos Forecast: BULLISH               │
│ XGBoost BUY Probability: 84%            │
│ Final Confidence: 82%                   │
├─────────────────────────────────────────┤
│ AI Decision: BUY                        │
│ Risk Shield: APPROVED                   │
│ Position: $8.00                         │
├─────────────────────────────────────────┤
│ Recent Trades                           │
│ #181  BUY   +$0.12                      │
│ #182  HOLD   --                         │
│ #183  SELL  -$0.08                      │
│ #184  BUY   +$0.08                      │
└─────────────────────────────────────────┘
```

---

# 35. Suggested Technology Stack

## Backend

- Python
- FastAPI
- Pandas
- NumPy
- scikit-learn
- XGBoost
- PyTorch
- Hugging Face ecosystem where appropriate

## Forecasting

- Chronos-2 as the primary pretrained forecasting candidate
- TimesFM or another model as an experimental comparison if hardware permits

## Database

- SQLite for the first version
- PostgreSQL if scaling becomes necessary

## Exchange integration

- Exchange REST/WebSocket API
- A well-maintained exchange client library where appropriate

## Frontend

- React
- TypeScript
- Vite
- Charting library

## Local environment

- Windows/Linux PC
- Python virtual environment
- `.env` for API credentials

---

# 36. Suggested Project Structure

```text
ai-trading-agent/
│
├── app/
│   ├── main.py
│   │
│   ├── data/
│   │   ├── market_data.py
│   │   ├── preprocessing.py
│   │   └── indicators.py
│   │
│   ├── forecasting/
│   │   ├── chronos_model.py
│   │   └── forecast_features.py
│   │
│   ├── ai/
│   │   ├── feature_engineering.py
│   │   ├── train.py
│   │   ├── predict.py
│   │   └── model.pkl
│   │
│   ├── regime/
│   │   └── detector.py
│   │
│   ├── strategy/
│   │   └── strategy.py
│   │
│   ├── survival/
│   │   └── survival_engine.py
│   │
│   ├── risk/
│   │   └── risk_manager.py
│   │
│   ├── execution/
│   │   └── broker.py
│   │
│   ├── portfolio/
│   │   └── portfolio.py
│   │
│   ├── database/
│   │   └── database.py
│   │
│   └── monitoring/
│       └── logger.py
│
├── backtesting/
│   ├── engine.py
│   ├── walk_forward.py
│   └── metrics.py
│
├── dashboard/
│   └── React application
│
├── models/
│
├── data/
│
├── tests/
│
├── .env
├── requirements.txt
└── README.md
```

---

# 37. Autonomous Operating Loop

The live system can run approximately as follows:

```text
START
  ↓
Load configuration
  ↓
Connect to exchange
  ↓
Check account status
  ↓
Download/receive latest market data
  ↓
Validate data
  ↓
Calculate indicators
  ↓
Generate Chronos forecast
  ↓
Generate XGBoost prediction
  ↓
Detect market regime
  ↓
Calculate confidence
  ↓
Update survival state
  ↓
Generate trade proposal
  ↓
Risk Shield
  │
  ├── REJECT → Log → Wait
  │
  └── ALLOW
          ↓
      Execute order
          ↓
      Verify fill
          ↓
      Update portfolio
          ↓
      Log trade
          ↓
      Monitor position
          ↓
      Repeat
```

The system can operate automatically on each new candle.

---

# 38. Failure Handling

A professional autonomous system must assume that components can fail.

## Internet failure

```text
No reliable market data
→ Do not create new orders
→ Preserve current state
→ Retry connection
```

## Exchange API failure

```text
API unavailable
→ Disable new entries
→ Log error
→ Retry with controlled backoff
```

## Invalid market data

```text
Data validation failure
→ Reject signal
→ Do not trade
```

## PC restart

The system should recover state from the database.

## Duplicate order

Use unique order IDs and state reconciliation.

## Unexpected balance

Compare local portfolio state with exchange account state before resuming.

---

# 39. Emergency Stop

Even though the project is autonomous, it should have a hard emergency mechanism.

Possible triggers:

- Severe API malfunction
- Unexpected account state
- Software corruption
- Abnormal price feed
- Repeated execution failures
- Risk limit breach

The emergency stop should be outside the AI decision logic.

---

# 40. Security

API credentials must never be hard-coded.

Use:

```text
.env
```

Example:

```text
EXCHANGE_API_KEY=...
EXCHANGE_API_SECRET=...
```

The API key should have only the permissions required by the system.

For development, use an exchange's sandbox/test environment where available.

---

# 41. Development Phases

## Phase 1 — Data Engine

Build:

- Historical data downloader
- Data validation
- Local storage
- OHLCV processing

Do not trade.

---

## Phase 2 — Technical Strategy

Implement:

- RSI
- EMA
- MACD
- ATR
- Volume
- Basic BUY/SELL/HOLD logic

Backtest it.

---

## Phase 3 — Chronos Integration

Add:

- Chronos-2 inference
- Forecast generation
- Forecast-derived features

Compare forecast behavior against simple baselines.

---

## Phase 4 — XGBoost

Create:

- Training dataset
- Target labels
- Feature pipeline
- XGBoost classifier
- Probability output

Perform chronological validation.

---

## Phase 5 — Risk Shield

Implement:

- Position sizing
- Stop rules
- Daily loss limit
- Exposure limit
- Volatility restriction
- Emergency stop

---

## Phase 6 — Survival Simulation

Implement:

- $50 virtual starting capital
- Reward function
- Drawdown penalty
- Loss penalty
- Survival state
- Episode termination

---

## Phase 7 — Backtesting Engine

Add:

- Walk-forward testing
- Fees
- Slippage
- Spread assumptions
- Execution delay
- Metrics

---

## Phase 8 — Paper Trading

Run the complete system using simulated orders with live market data.

No real capital.

---

## Phase 9 — Controlled Live Experiment

Only after successful testing:

- Use a small amount of capital.
- Use spot trading.
- No leverage.
- Keep hard risk limits active.
- Monitor logs and execution.

The live system should not be presented as guaranteed to make money.

---

# 42. What Makes This Project Different?

The project is not simply:

> "Bitcoin price prediction using AI."

It combines several engineering concepts:

```text
Time-Series Foundation Model
            +
Machine Learning
            +
Technical Analysis
            +
Market Regime Detection
            +
Confidence Estimation
            +
Survival-Based Objective
            +
Deterministic Risk Management
            +
Autonomous Execution
            +
Explainability
            +
Continuous Evaluation
```

The **survival objective + independent Risk Shield** is the main research-oriented idea.

---

# 43. Research Hypothesis

### Hypothesis

> An autonomous trading agent that explicitly penalizes capital depletion and drawdown may preserve capital more effectively than an otherwise similar agent optimized primarily for trading return.

This hypothesis must be tested experimentally. It should not be assumed to be true.

---

# 44. Experimental Design

Create controlled experiments.

### Experiment A

Technical strategy only.

### Experiment B

XGBoost strategy.

### Experiment C

Chronos + XGBoost.

### Experiment D

Chronos + XGBoost + Risk Shield.

### Experiment E

Chronos + XGBoost + Risk Shield + Survival objective.

Use the same:

- Data
- Starting capital
- Trading costs
- Time period
- Evaluation metrics

Then analyze the differences.

---

# 45. Questions the Project Should Answer

1. Does Chronos improve forecasting features?
2. Does adding Chronos improve trading decisions?
3. Does the Risk Shield reduce maximum drawdown?
4. Does the survival objective reduce catastrophic losses?
5. Does survival optimization reduce profitability by making the agent too conservative?
6. How does the system behave during bull markets?
7. How does it behave during bear markets?
8. How does it behave during sideways markets?
9. What happens during extreme volatility?
10. How sensitive is performance to transaction costs?
11. How sensitive is the system to confidence thresholds?
12. Does the system remain useful on unseen data?
13. How long does the simulated agent survive?
14. How often does the Risk Shield reject AI signals?
15. What types of predictions does the AI get wrong?

---

# 46. Major Viva Questions

## Q1. What is the main objective?

To develop an autonomous BTC/USDT trading system that combines time-series forecasting, machine learning, risk management, and a survival-oriented objective.

## Q2. Why Chronos-2?

It provides a pretrained time-series forecasting component that can extract future-oriented information from historical sequences without requiring the project to train a large forecasting model from scratch.

## Q3. Is Chronos-2 a trading model?

No. It is used as a forecasting component. Its outputs become features for the trading decision layer.

## Q4. Why XGBoost?

XGBoost works well with structured tabular features and can combine technical indicators, market-state variables, and model-generated features.

## Q5. Why not directly trade from Chronos?

A forecast does not automatically account for trading costs, risk, position sizing, market regime, or whether the predicted movement is large enough to justify a trade.

## Q6. What is survival-based trading?

It is an objective where the simulated agent is rewarded for useful returns but penalized for drawdown, excessive risk, and capital depletion.

## Q7. What does "death" mean?

It means the simulated trading episode terminates after the capital reaches the defined failure condition.

## Q8. Can the AI guarantee profit?

No.

## Q9. Why use $50?

It provides a simple fixed starting capital for simulation and a small-scale experimental setup. It does not imply that $50 is sufficient for profitable real-world trading.

## Q10. Why no leverage?

To reduce liquidation and risk complexity in the first version.

## Q11. How do you prevent overfitting?

Use chronological train/validation/test splits, walk-forward evaluation, out-of-sample testing, regularization, and controlled feature selection.

## Q12. What is data leakage?

Using information during training or prediction that would not have been available at the actual decision time.

## Q13. What if the AI gives a wrong signal?

The Risk Shield can reject the trade, reduce position size, or prevent further trading depending on the risk state.

## Q14. Why is a separate Risk Shield needed?

An ML model is probabilistic and can make mistakes. Deterministic risk rules provide an independent safety boundary.

## Q15. How will you know whether the project works?

By testing on unseen data and evaluating return, drawdown, profit factor, Sharpe ratio, win rate, trade count, costs, and survival duration.

## Q16. What if the backtest gives extremely high profit?

Investigate data leakage, look-ahead bias, overfitting, unrealistic execution assumptions, and insufficient out-of-sample testing before trusting the result.

## Q17. What happens if the internet stops?

The system should stop opening new trades until reliable market data and exchange connectivity are restored.

## Q18. What happens if the PC crashes?

Persist portfolio and trade state in a database and reconcile state with the exchange before resuming.

## Q19. Can the AI change its own risk limits?

No. Critical risk controls should be outside the model's ability to modify.

## Q20. Is the project guaranteed to make money?

No. The objective is to build and experimentally evaluate an autonomous trading architecture, not to guarantee financial returns.

---

# 47. Potential Improvements

Future versions can investigate:

- ETH/USDT
- Multi-asset trading
- Transformer-based trading models
- Reinforcement learning
- PPO-based simulated agents
- Order-book features
- Sentiment features
- On-chain features
- News-event detection
- Advanced portfolio optimization
- Bayesian uncertainty
- Ensemble forecasting
- Online learning
- Distributed backtesting

These should be added only after the baseline system is stable.

---

# 48. Recommended First Version

Do not build everything simultaneously.

The first working version should be:

```text
BTC/USDT
1-hour candles
       ↓
OHLCV
       ↓
Technical indicators
       +
Chronos-2
       ↓
XGBoost
       ↓
BUY / SELL / HOLD
       ↓
Risk Shield
       ↓
Backtesting
       ↓
Paper Trading
```

Then add:

```text
Market Regime
       ↓
Confidence
       ↓
Survival Engine
       ↓
Explainability Dashboard
```

Finally, investigate controlled live execution.

---

# 49. Final Project Definition

> **We are developing a locally deployed autonomous AI-based cryptocurrency trading agent for BTC/USDT that combines pretrained time-series forecasting, machine-learning-based trade classification, technical market analysis, market-regime detection, confidence estimation, survival-oriented capital preservation, deterministic risk management, and automated exchange execution. The system is designed to operate without manual approval for individual trades while keeping critical risk controls outside the AI. Its effectiveness will be evaluated through realistic walk-forward backtesting, paper trading, and controlled experiments measuring both profitability and capital preservation.**

---

# 50. One-Line Explanation for Viva

> **"Our project is an autonomous BTC/USDT trading agent that uses AI to identify trading opportunities, but uses a separate risk shield and survival objective to make capital preservation as important as profit."**

---

# 51. Final Development Philosophy

The most important principle is:

```text
Predict → Decide → Protect → Execute → Measure → Learn
```

Not:

```text
Predict → Trade blindly
```

The project should prioritize:

1. Correct data handling
2. No data leakage
3. Realistic backtesting
4. Independent risk controls
5. Explainable decisions
6. Reproducible experiments
7. Paper trading before live trading
8. Controlled deployment
9. Continuous monitoring
10. Scientific evaluation rather than assuming profitability

This makes the project a serious **AI/ML + autonomous systems + financial computing research project**, rather than just a basic crypto bot.
