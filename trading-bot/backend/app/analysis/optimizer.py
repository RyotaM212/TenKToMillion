import json
from datetime import date

from app.analysis.backtester import Backtester
from app.db import execute, fetch_all
from app.models import STRATEGY_NAMES


class Optimizer:
    def __init__(self) -> None:
        self.backtester = Backtester()

    def run(self) -> dict[str, int]:
        created = 0
        for strategy_name in STRATEGY_NAMES:
            proposed = {
                "take_profit_rate": 0.12,
                "stop_loss_rate": 0.06,
                "entry_start_time": "09:15",
                "entry_end_time": "10:20",
                "volume_spike_threshold": 3.5,
                "breakout_threshold": 0.012,
                "vwap_exit_enabled": True,
            }
            result = self.backtester.mini_backtest(strategy_name, proposed)
            adopted = result["profit_rate"] > 0 and result["max_drawdown"] >= -0.03 and result["trade_count"] >= 3
            execute(
                """
                INSERT INTO strategy_experiments(
                  experiment_date, strategy_name, base_params_id, proposed_params_json,
                  backtest_result_json, adopted, reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    date.today().isoformat(),
                    strategy_name,
                    None,
                    json.dumps(proposed, ensure_ascii=False),
                    json.dumps(result, ensure_ascii=False),
                    1 if adopted else 0,
                    "採用条件を満たすMVP改善案" if adopted else "採用条件未達",
                ),
            )
            created += 1
        return {"created": created}


def latest_experiments() -> list[dict]:
    return fetch_all("SELECT * FROM strategy_experiments ORDER BY created_at DESC LIMIT 20")
