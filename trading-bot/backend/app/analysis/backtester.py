from __future__ import annotations

from app.db import fetch_all


class Backtester:
    def mini_backtest(self, strategy_name: str, proposed_params: dict[str, float | str | bool]) -> dict[str, float | str]:
        rows = fetch_all("SELECT pnl FROM paper_trades WHERE strategy_name = ? ORDER BY created_at DESC LIMIT 100", (strategy_name,))
        pnl_values = [float(row["pnl"]) for row in rows]
        total_pnl = round(sum(pnl_values), 2)
        trade_count = len(pnl_values)
        max_drawdown = self._max_drawdown(pnl_values)
        return {
            "strategy_name": strategy_name,
            "profit_rate": round(total_pnl / 10_000, 4),
            "max_drawdown": max_drawdown,
            "trade_count": trade_count,
            "note": "Based on recent paper-trade logs. Historical replay should be added before live trading.",
            "params": str(proposed_params),
        }

    def _max_drawdown(self, pnl_values: list[float]) -> float:
        equity = 0.0
        peak = 0.0
        max_drawdown = 0.0
        for pnl in pnl_values:
            equity += pnl
            peak = max(peak, equity)
            max_drawdown = min(max_drawdown, equity - peak)
        return round(max_drawdown / 10_000, 4)
