// ── Agent types ───────────────────────────────────────────────────────────────

export interface AgentState {
  agent_id:          string;
  name:              string;
  description:       string;
  status:            'ACTIVE' | 'DEGRADED' | 'DEAD';
  allocated_capital: number;
  cash:              number;
  equity:            number;
  reward_score:      number;
  trade_count:       number;
  wins:              number;
  losses:            number;
  win_rate_pct:      number;
  total_pnl:         number;
  max_drawdown_pct:  number;
  confidence_hurdle: number;
  size_multiplier:   number;
  has_position:      boolean;
  last_decision?: {
    action:      string;
    confidence:  number;
    rationale?:  string;
    timestamp?:  number;
  };
}

// ── Market Research types ─────────────────────────────────────────────────────

export interface FearGreed {
  score:     number;
  label:     string;
  sentiment: number;  // contrarian, -1 to +1
}

export interface Orderbook {
  bid_volume: number;
  ask_volume: number;
  imbalance:  number;  // -1 to +1
  best_bid:   number;
  best_ask:   number;
  spread_pct: number;
}

export interface CoinGecko {
  price_usd:      number;
  market_cap:     number;
  volume_24h:     number;
  change_24h_pct: number;
  momentum:       number;  // -1 to +1
}

export interface NewsData {
  headlines:      string[];
  bullish_count:  number;
  bearish_count:  number;
  news_sentiment: number;
}

export interface MarketResearch {
  timestamp:   number;
  fear_greed:  FearGreed;
  orderbook:   Orderbook;
  coingecko:   CoinGecko;
  news:        NewsData;
}

// ── System status ─────────────────────────────────────────────────────────────

export interface SystemStatus {
  status:                string;
  broker_mode:           string;
  live_trading_enabled:  boolean;
  auto_running:          boolean;
  cycle_count:           number;
  total_equity:          number;
  active_agents:         number;
  exchange_free_usdt:    number;
  exchange_free_btc:     number;
  symbol:                string;
  latest_price:          number;
  regime:                string;
}

// ── Broker status ─────────────────────────────────────────────────────────────

export interface BrokerStatus {
  mode:                   string;
  sandbox:                boolean;
  success:                boolean;
  free_usdt:              number;
  total_usdt:             number;
  free_btc:               number;
  total_btc:              number;
  max_allocated_capital:  number;
  min_notional:           number;
  error:                  string | null;
}

// ── Trade record ──────────────────────────────────────────────────────────────

export interface AgentTrade {
  id:               number;
  timestamp:        number;
  agent_id:         string;
  agent_name:       string;
  symbol:           string;
  action:           string;
  confidence:       number;
  entry_price:      number | null;
  exit_price:       number | null;
  position_size:    number;
  qty:              number;
  gross_pnl:        number;
  fees:             number;
  net_pnl:          number;
  reward_delta:     number;
  new_reward_score: number;
  regime:           string;
  rationale:        string;
  notes:            string;
}
