from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable

from app.config import get_settings


SCHEMA = """
CREATE TABLE IF NOT EXISTS app_state (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS candidates (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  trade_date TEXT NOT NULL,
  symbol TEXT NOT NULL,
  symbol_name TEXT NOT NULL,
  score REAL NOT NULL,
  strategy_name TEXT NOT NULL,
  volume_spike_score REAL NOT NULL,
  price_change_score REAL NOT NULL,
  gap_up_score REAL NOT NULL,
  volatility_score REAL NOT NULL,
  news_score REAL NOT NULL,
  liquidity_score REAL NOT NULL,
  selected_reason TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS market_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  symbol TEXT NOT NULL,
  symbol_name TEXT NOT NULL,
  snapshot_time TEXT NOT NULL,
  price REAL NOT NULL,
  volume INTEGER NOT NULL,
  vwap REAL NOT NULL,
  open REAL NOT NULL,
  high REAL NOT NULL,
  low REAL NOT NULL,
  close REAL NOT NULL,
  previous_close REAL NOT NULL,
  news_score REAL NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS paper_trades (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  trade_date TEXT NOT NULL,
  mode TEXT NOT NULL,
  strategy_name TEXT NOT NULL,
  symbol TEXT NOT NULL,
  symbol_name TEXT NOT NULL,
  entry_time TEXT NOT NULL,
  entry_price REAL NOT NULL,
  exit_time TEXT NOT NULL,
  exit_price REAL NOT NULL,
  quantity INTEGER NOT NULL,
  pnl REAL NOT NULL,
  pnl_rate REAL NOT NULL,
  exit_reason TEXT NOT NULL,
  candidate_score REAL NOT NULL,
  entry_reason TEXT NOT NULL,
  max_unrealized_profit REAL NOT NULL,
  max_unrealized_loss REAL NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS paper_positions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  mode TEXT NOT NULL,
  strategy_name TEXT NOT NULL,
  symbol TEXT NOT NULL,
  quantity INTEGER NOT NULL,
  entry_price REAL NOT NULL,
  entry_time TEXT NOT NULL,
  current_price REAL NOT NULL,
  unrealized_pnl REAL NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS daily_reports (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  trade_date TEXT NOT NULL,
  mode TEXT NOT NULL,
  strategy_name TEXT NOT NULL,
  start_cash REAL NOT NULL,
  end_cash REAL NOT NULL,
  locked_profit REAL NOT NULL,
  daily_pnl REAL NOT NULL,
  daily_pnl_rate REAL NOT NULL,
  trade_count INTEGER NOT NULL,
  win_count INTEGER NOT NULL,
  lose_count INTEGER NOT NULL,
  win_rate REAL NOT NULL,
  max_drawdown REAL NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS strategy_params (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  strategy_name TEXT NOT NULL,
  active_from TEXT NOT NULL,
  take_profit_rate REAL NOT NULL,
  stop_loss_rate REAL NOT NULL,
  entry_start_time TEXT NOT NULL,
  entry_end_time TEXT NOT NULL,
  volume_spike_threshold REAL NOT NULL,
  breakout_threshold REAL NOT NULL,
  vwap_exit_enabled INTEGER NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS strategy_experiments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  experiment_date TEXT NOT NULL,
  strategy_name TEXT NOT NULL,
  base_params_id INTEGER,
  proposed_params_json TEXT NOT NULL,
  backtest_result_json TEXT NOT NULL,
  adopted INTEGER NOT NULL,
  reason TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def dict_factory(cursor: sqlite3.Cursor, row: tuple[Any, ...]) -> dict[str, Any]:
    return {column[0]: row[index] for index, column in enumerate(cursor.description)}


@contextmanager
def get_connection():
    settings = get_settings()
    db_path = Path(settings.database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = dict_factory
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        settings = get_settings()
        conn.executescript(SCHEMA)
        conn.execute("INSERT OR IGNORE INTO app_state(key, value) VALUES('mode', 'YOLO_MODE')")
        conn.execute("INSERT OR IGNORE INTO app_state(key, value) VALUES('data_source', ?)", (settings.data_source,))
        conn.execute("INSERT OR IGNORE INTO app_state(key, value) VALUES('active_strategy', 'HybridStrategy')")


def fetch_all(query: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
    with get_connection() as conn:
        return list(conn.execute(query, tuple(params)).fetchall())


def fetch_one(query: str, params: Iterable[Any] = ()) -> dict[str, Any] | None:
    with get_connection() as conn:
        return conn.execute(query, tuple(params)).fetchone()


def execute(query: str, params: Iterable[Any] = ()) -> None:
    with get_connection() as conn:
        conn.execute(query, tuple(params))


if __name__ == "__main__":
    init_db()
    print("SQLite initialized.")
