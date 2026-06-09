from app.db import fetch_all


class StrategyEvaluator:
    def comparison(self) -> list[dict]:
        return fetch_all(
            """
            SELECT
              strategy_name,
              ROUND(SUM(daily_pnl), 2) AS total_pnl,
              ROUND(AVG(win_rate), 4) AS avg_win_rate,
              SUM(trade_count) AS trade_count,
              ROUND(MIN(max_drawdown), 2) AS max_drawdown
            FROM daily_reports
            GROUP BY strategy_name
            ORDER BY total_pnl DESC
            """
        )

    def mode_comparison(self) -> list[dict]:
        return fetch_all(
            """
            SELECT
              mode,
              ROUND(SUM(daily_pnl), 2) AS total_pnl,
              ROUND(AVG(win_rate), 4) AS avg_win_rate,
              SUM(trade_count) AS trade_count,
              ROUND(MAX(locked_profit), 2) AS locked_profit
            FROM daily_reports
            GROUP BY mode
            ORDER BY total_pnl DESC
            """
        )
