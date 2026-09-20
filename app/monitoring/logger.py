"""
Logging configuration — structured logging to stdout + rotating file.

Usage (in main.py or any entry point):
    from app.monitoring.logger import setup_logging
    setup_logging()
"""
from __future__ import annotations
import logging
import logging.handlers
import os
import sys
from pathlib import Path


def setup_logging(level: str | None = None) -> None:
    """Configure root logger. Call once at startup."""
    log_level = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    numeric = getattr(logging, log_level, logging.INFO)

    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt, datefmt=datefmt)

    root = logging.getLogger()
    root.setLevel(numeric)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    root.addHandler(ch)

    # File handler (rotating, 5 MB × 3 files)
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    fh = logging.handlers.RotatingFileHandler(
        log_dir / "trading_agent.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    fh.setFormatter(formatter)
    root.addHandler(fh)

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
