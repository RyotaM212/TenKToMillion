from __future__ import annotations

from collections import defaultdict
from datetime import date

from app.config import get_settings
from app.db import execute, fetch_all
from app.models import CAPITAL_MODES, STRATEGY_NAMES


class DailyAnalyzer:
    def run(self) -> dict[str, int]:
        today = date.today().isoformat()
        created = 0
        initial_cash = float(get_settings().initial_cash)
        for mode in CAPITAL_MODES:
            for strategy_name in STRATEGY_NAMES:
                execute(
                    "DELETE FROM daily_reports WHERE trade_date = ? AND mode = ? AND strategy_name = ?",
                    (today, mode, strategy_name),
                )
                trades = fetch_all(
                    """
                    SELECT * FROM paper_trades
                    WHERE trade_date = ? AND mode = ? AND strategy_name = ?
                    """,
                    (today, mode, strategy_name),
                )
                total_pnl = sum(float(row["pnl"]) for row in trades)
                win_count = sum(1 for row in trades if float(row["pnl"]) > 0)
                lose_count = sum(1 for row in trades if float(row["pnl"]) < 0)
                locked_profit = sum(max(float(row["pnl"]) * 0.5, 0) for row in trades) if mode == "LOCK_PROFIT_MODE" else 0
                max_drawdown = self._max_drawdown([float(row["pnl"]) for row in trades])
                trade_count = len(trades)
                execute(
                    """
                    INSERT INTO daily_reports(
                      trade_date, mode, strategy_name, start_cash, end_cash, locked_profit,
                      daily_pnl, daily_pnl_rate, trade_count, win_count, lose_count, win_rate, max_drawdown
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        today,
                        mode,
                        strategy_name,
                        initial_cash,
                        initial_cash + total_pnl,
                        locked_profit,
                        total_pnl,
                        round(total_pnl / initial_cash, 4),
                        trade_count,
                        win_count,
                        lose_count,
                        round(win_count / trade_count, 4) if trade_count else 0,
                        max_drawdown,
                    ),
                )
                created += 1
        return {"created": created}

    def summarize_by_strategy(self) -> list[dict[str, float | str]]:
        rows = fetch_all("SELECT * FROM daily_reports ORDER BY created_at DESC")
        grouped: dict[str, dict[str, float | str]] = defaultdict(lambda: {"strategy_name": "", "pnl": 0.0, "trades": 0.0, "win_rate": 0.0})
        for row in rows:
            item = grouped[row["strategy_name"]]
            item["strategy_name"] = row["strategy_name"]
            item["pnl"] = float(item["pnl"]) + float(row["daily_pnl"])
            item["trades"] = float(item["trades"]) + float(row["trade_count"])
            item["win_rate"] = max(float(item["win_rate"]), float(row["win_rate"]))
        return list(grouped.values())

    def _max_drawdown(self, pnl_values: list[float]) -> float:
        peak = 0.0
        equity = 0.0
        max_drawdown = 0.0
        for pnl in pnl_values:
            equity += pnl
            peak = max(peak, equity)
            max_drawdown = min(max_drawdown, equity - peak)
        return round(max_drawdown, 2)
