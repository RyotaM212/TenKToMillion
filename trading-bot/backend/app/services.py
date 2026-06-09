from datetime import date

from app.analysis.daily_analyzer import DailyAnalyzer
from app.analysis.optimizer import Optimizer
from app.collectors.jquants_collector import JQuantsCollector
from app.collectors.market_data_collector import MarketDataCollector
from app.collectors.mock_collector import MockCollector
from app.collectors.yahoo_collector import YahooCollector
from app.config import get_settings
from app.db import execute, fetch_all, fetch_one, init_db
from app.models import CAPITAL_MODES, STRATEGY_NAMES, StrategyParams
from app.screening.universe_filter import UniverseFilter
from app.strategies import build_strategies
from app.trading.execution_engine import ExecutionEngine


def get_collector() -> MarketDataCollector:
    state = fetch_one("SELECT value FROM app_state WHERE key = 'data_source'")
    source = state["value"] if state else get_settings().data_source
    if source == "jquants":
        return JQuantsCollector()
    if source == "yahoo":
        return YahooCollector()
    return MockCollector()


def set_app_state(key: str, value: str) -> dict[str, str]:
    allowed_values = {
        "mode": CAPITAL_MODES,
        "data_source": ("mock", "yahoo", "jquants"),
        "active_strategy": STRATEGY_NAMES,
    }
    if key not in allowed_values:
        raise ValueError(f"Unknown app state key: {key}")
    if value not in allowed_values[key]:
        raise ValueError(f"Invalid {key}: {value}")
    execute("INSERT INTO app_state(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, value))
    return {"key": key, "value": value}


def persist_snapshot(snapshot) -> None:
    execute(
        """
        INSERT INTO market_snapshots(
          symbol, symbol_name, snapshot_time, price, volume, vwap, open, high, low,
          close, previous_close, news_score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            snapshot.symbol,
            snapshot.symbol_name,
            snapshot.snapshot_time.isoformat(),
            snapshot.price,
            snapshot.volume,
            snapshot.vwap,
            snapshot.open,
            snapshot.high,
            snapshot.low,
            snapshot.close,
            snapshot.previous_close,
            snapshot.news_score,
        ),
    )


def run_screening() -> dict[str, int]:
    init_db()
    execute("DELETE FROM candidates WHERE trade_date = ?", (date.today().isoformat(),))
    collector = get_collector()
    snapshots = collector.fetch_ranking()
    for snapshot in snapshots:
        persist_snapshot(snapshot)

    created = 0
    universe_filter = UniverseFilter()
    for strategy in build_strategies():
        candidates = universe_filter.build_candidates(snapshots, strategy)
        for candidate in candidates[:20]:
            execute(
                """
                INSERT INTO candidates(
                  trade_date, symbol, symbol_name, score, strategy_name,
                  volume_spike_score, price_change_score, gap_up_score, volatility_score,
                  news_score, liquidity_score, selected_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    candidate.trade_date,
                    candidate.symbol,
                    candidate.symbol_name,
                    candidate.score,
                    candidate.strategy_name,
                    candidate.volume_spike_score,
                    candidate.price_change_score,
                    candidate.gap_up_score,
                    candidate.volatility_score,
                    candidate.news_score,
                    candidate.liquidity_score,
                    candidate.selected_reason,
                ),
            )
            created += 1
    return {"created": created}


def run_paper_trade() -> dict[str, int]:
    engine = ExecutionEngine(get_collector(), float(get_settings().initial_cash))
    return engine.run_paper_trades()


def run_analysis() -> dict[str, int]:
    return DailyAnalyzer().run()


def run_optimization() -> dict[str, int]:
    return Optimizer().run()


def dashboard() -> dict:
    init_db()
    reports = fetch_all("SELECT * FROM daily_reports ORDER BY created_at DESC LIMIT 50")
    trades = fetch_all("SELECT * FROM paper_trades ORDER BY created_at DESC LIMIT 50")
    candidates = fetch_all("SELECT * FROM candidates ORDER BY score DESC LIMIT 20")
    positions = fetch_all("SELECT * FROM paper_positions ORDER BY updated_at DESC")
    experiments = fetch_all("SELECT * FROM strategy_experiments ORDER BY created_at DESC LIMIT 20")
    llm_report = fetch_one("SELECT * FROM llm_analysis_reports ORDER BY created_at DESC LIMIT 1")
    state_rows = fetch_all("SELECT key, value FROM app_state")
    state = {row["key"]: row["value"] for row in state_rows}
    active_mode = state.get("mode", "YOLO_MODE")
    active_strategy = state.get("active_strategy", "HybridStrategy")
    active_reports = [row for row in reports if row["mode"] == active_mode and row["strategy_name"] == active_strategy]

    total_pnl = sum(float(row["daily_pnl"]) for row in active_reports)
    latest = active_reports[0] if active_reports else None
    return {
        "current_asset": float(get_settings().initial_cash) + total_pnl,
        "buying_power": float(get_settings().initial_cash) + total_pnl,
        "locked_profit": sum(float(row["locked_profit"]) for row in active_reports),
        "today_pnl": float(latest["daily_pnl"]) if latest else 0,
        "total_pnl": total_pnl,
        "win_rate": float(latest["win_rate"]) if latest else 0,
        "max_drawdown": min([float(row["max_drawdown"]) for row in active_reports], default=0),
        "mode": active_mode,
        "active_strategy": active_strategy,
        "data_source": state.get("data_source", "mock"),
        "candidates": candidates,
        "positions": positions,
        "trades": trades,
        "reports": reports,
        "experiments": experiments,
        "llm_report": llm_report,
    }


def default_strategy_params() -> list[dict]:
    return [
        {
            "strategy_name": strategy.name,
            "active_from": "MVP",
            **StrategyParams(strategy_name=strategy.name).__dict__,
        }
        for strategy in build_strategies()
    ]
