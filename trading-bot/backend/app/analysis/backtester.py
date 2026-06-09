from __future__ import annotations

class Backtester:
    def mini_backtest(self, strategy_name: str, proposed_params: dict[str, float | str | bool]) -> dict[str, float | str]:
        return {
            "strategy_name": strategy_name,
            "profit_rate": 0.03,
            "max_drawdown": -0.02,
            "trade_count": 4,
            "note": "MVP stub using paper-trade logs; replace with historical replay before production.",
            "params": str(proposed_params),
        }
