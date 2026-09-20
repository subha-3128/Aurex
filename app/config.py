"""
Config — single source of truth for environment variables.

Import this anywhere in the project:
    from app.config import cfg
    print(cfg.symbol)
"""
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()   # reads .env if present, no-op if missing


@dataclass(frozen=True)
class Config:
    # Data
    symbol: str            = field(default_factory=lambda: os.getenv("SYMBOL", "BTC/USDT"))
    timeframe: str         = field(default_factory=lambda: os.getenv("TIMEFRAME", "1h"))
    initial_fetch_bars: int = field(default_factory=lambda: int(os.getenv("INITIAL_FETCH_BARS", "2000")))
    data_dir: Path         = field(default_factory=lambda: Path(os.getenv("DATA_DIR", "data/")))
    db_path: str           = field(default_factory=lambda: os.getenv("DB_PATH", "data/trading.db"))

    # Exchange
    api_key: str           = field(default_factory=lambda: os.getenv("EXCHANGE_API_KEY", ""))
    api_secret: str        = field(default_factory=lambda: os.getenv("EXCHANGE_API_SECRET", ""))
    sandbox: bool          = field(default_factory=lambda: os.getenv("EXCHANGE_SANDBOX", "true").lower() == "true")
    live_trading_enabled: bool = field(default_factory=lambda: os.getenv("LIVE_TRADING_ENABLED", "false").lower() == "true")
    max_allocated_capital: float = field(default_factory=lambda: float(os.getenv("MAX_ALLOCATED_CAPITAL", os.getenv("INITIAL_CAPITAL", "50.0"))))
    min_notional_usd: float = field(default_factory=lambda: float(os.getenv("MIN_NOTIONAL_USD", "10.0")))

    # Model
    model_dir: Path        = field(default_factory=lambda: Path(os.getenv("MODEL_DIR", "models/")))
    chronos_model: str     = field(default_factory=lambda: os.getenv("CHRONOS_MODEL", "amazon/chronos-bolt-small"))
    chronos_context: int   = field(default_factory=lambda: int(os.getenv("CHRONOS_CONTEXT_LEN", "128")))
    forecast_horizon: int  = field(default_factory=lambda: int(os.getenv("FORECAST_HORIZON", "4")))

    # Trading
    initial_capital: float = field(default_factory=lambda: float(os.getenv("INITIAL_CAPITAL", "50.0")))
    max_risk_per_trade: float = field(default_factory=lambda: float(os.getenv("MAX_RISK_PER_TRADE", "0.01")))
    max_daily_loss: float  = field(default_factory=lambda: float(os.getenv("MAX_DAILY_LOSS", "0.04")))
    max_open_positions: int = field(default_factory=lambda: int(os.getenv("MAX_OPEN_POSITIONS", "1")))
    taker_fee: float       = field(default_factory=lambda: float(os.getenv("TAKER_FEE", "0.001")))
    slippage: float        = field(default_factory=lambda: float(os.getenv("SLIPPAGE", "0.0005")))
    label_threshold: float = field(default_factory=lambda: float(os.getenv("LABEL_THRESHOLD", "0.003")))

    # Survival
    survival_alpha: float  = field(default_factory=lambda: float(os.getenv("SURVIVAL_ALPHA", "1.0")))
    survival_beta: float   = field(default_factory=lambda: float(os.getenv("SURVIVAL_BETA", "0.5")))
    survival_gamma: float  = field(default_factory=lambda: float(os.getenv("SURVIVAL_GAMMA", "0.2")))
    survival_delta: float  = field(default_factory=lambda: float(os.getenv("SURVIVAL_DELTA", "0.3")))
    survival_floor: float  = field(default_factory=lambda: float(os.getenv("SURVIVAL_FLOOR", "0.05")))

    # API
    api_host: str          = field(default_factory=lambda: os.getenv("API_HOST", "0.0.0.0"))
    api_port: int          = field(default_factory=lambda: int(os.getenv("API_PORT", "8000")))

    # Automation & Loop
    auto_loop_interval_sec: int = field(default_factory=lambda: int(os.getenv("AUTO_LOOP_INTERVAL_SEC", "30")))

    # Logging
    log_level: str         = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))


cfg = Config()
