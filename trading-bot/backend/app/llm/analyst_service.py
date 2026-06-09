from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any

from app.analysis.backtester import Backtester
from app.db import execute, fetch_all, fetch_one
from app.llm.analyst_client import build_analyst_client
from app.llm.prompt_builder import PromptBuilder
from app.llm.response_parser import ResponseParser
from app.llm.schemas import LlmAnalysisReport
from app.models import CAPITAL_MODES, STRATEGY_NAMES
from app.services import default_strategy_params


PROJECT_GOAL = "初期資金10000円から高リスク短期売買で資金増加を狙う。ただし初期はペーパートレードのみ。"


class AnalystService:
    def __init__(self) -> None:
        self.prompt_builder = PromptBuilder()
        self.response_parser = ResponseParser()
        self.backtester = Backtester()

    def run_daily_analysis(self, analysis_date: date) -> LlmAnalysisReport:
        started_at = datetime.now().isoformat()
        execute(
            "INSERT INTO llm_analysis_runs(analysis_date, status, started_at) VALUES (?, ?, ?)",
            (analysis_date.isoformat(), "running", started_at),
        )
        run = fetch_one("SELECT id FROM llm_analysis_runs WHERE analysis_date = ? ORDER BY id DESC LIMIT 1", (analysis_date.isoformat(),))
        run_id = int(run["id"]) if run else 0

        try:
            payload = self._build_payload(analysis_date)
            prompt = self.prompt_builder.build_daily_analysis_prompt(payload)
            client = build_analyst_client()
            result = client.analyze(prompt)
            parsed = self.response_parser.parse(result.content)
            report_id = self._save_report(analysis_date, result.model_name, payload, parsed)
            backtest_result = self._save_strategy_experiment(analysis_date, parsed["proposed_params"])
            self._update_report_backtest(report_id, backtest_result)
            execute(
                """
                UPDATE llm_analysis_runs
                SET status = ?, finished_at = ?, token_usage_json = ?
                WHERE id = ?
                """,
                ("success", datetime.now().isoformat(), json.dumps(result.token_usage, ensure_ascii=False), run_id),
            )
            return self._row_to_report(fetch_one("SELECT * FROM llm_analysis_reports WHERE id = ?", (report_id,)))
        except Exception as exc:
            execute(
                """
                UPDATE llm_analysis_runs
                SET status = ?, finished_at = ?, error_message = ?
                WHERE id = ?
                """,
                ("failed", datetime.now().isoformat(), str(exc), run_id),
            )
            raise

    def backtest_latest_proposals(self) -> dict[str, int]:
        reports = fetch_all("SELECT * FROM llm_analysis_reports ORDER BY created_at DESC LIMIT 20")
        updated = 0
        for row in reports:
            proposed_params = json.loads(row["proposed_params_json"])
            backtest_result = self._save_strategy_experiment(date.fromisoformat(row["analysis_date"]), proposed_params)
            self._update_report_backtest(int(row["id"]), backtest_result)
            updated += 1
        return {"updated": updated}

    def reports(self) -> list[dict[str, Any]]:
        return fetch_all("SELECT * FROM llm_analysis_reports ORDER BY created_at DESC LIMIT 50")

    def latest_report(self) -> dict[str, Any] | None:
        return fetch_one("SELECT * FROM llm_analysis_reports ORDER BY created_at DESC LIMIT 1")

    def runs(self) -> list[dict[str, Any]]:
        return fetch_all("SELECT * FROM llm_analysis_runs ORDER BY created_at DESC LIMIT 50")

    def _build_payload(self, analysis_date: date) -> dict[str, Any]:
        date_text = analysis_date.isoformat()
        trades = fetch_all("SELECT * FROM paper_trades WHERE trade_date = ? ORDER BY created_at", (date_text,))
        candidates = fetch_all("SELECT * FROM candidates WHERE trade_date = ? ORDER BY score DESC LIMIT 50", (date_text,))
        reports = fetch_all("SELECT * FROM daily_reports WHERE trade_date = ? ORDER BY mode, strategy_name", (date_text,))
        recent_reports = fetch_all("SELECT * FROM daily_reports ORDER BY trade_date DESC, created_at DESC LIMIT 60")
        experiments = fetch_all("SELECT * FROM strategy_experiments ORDER BY created_at DESC LIMIT 20")

        total_pnl = sum(float(row["pnl"]) for row in trades)
        wins = sum(1 for row in trades if float(row["pnl"]) > 0)
        trade_count = len(trades)
        strategy_totals = self._group_pnl(reports, "strategy_name")

        return {
            "analysis_date": date_text,
            "project_goal": PROJECT_GOAL,
            "constraints": {
                "cash_only": True,
                "no_margin": True,
                "no_short": True,
                "no_leverage": True,
                "no_overnight": True,
                "max_positions": 1,
                "llm_cannot_place_orders": True,
            },
            "today_summary": {
                "total_pnl": round(total_pnl, 2),
                "trade_count": trade_count,
                "win_rate": round(wins / trade_count, 4) if trade_count else 0,
                "best_strategy": self._best_key(strategy_totals),
                "worst_strategy": self._worst_key(strategy_totals),
            },
            "trades": trades,
            "candidates": candidates,
            "strategy_reports": [row for row in reports if row["strategy_name"] in STRATEGY_NAMES],
            "mode_reports": [row for row in reports if row["mode"] in CAPITAL_MODES],
            "daily_reports": reports,
            "strategy_params": default_strategy_params(),
            "recent_reports": recent_reports,
            "recent_experiments": experiments,
        }

    def _save_report(self, analysis_date: date, model_name: str, payload: dict[str, Any], parsed: dict[str, Any]) -> int:
        execute(
            """
            INSERT INTO llm_analysis_reports(
              analysis_date, model_name, input_summary_json, output_json, summary_text,
              win_patterns, lose_patterns, risk_notes, improvement_suggestions,
              next_day_hypotheses, proposed_params_json, confidence_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                analysis_date.isoformat(),
                model_name,
                json.dumps(payload, ensure_ascii=False),
                json.dumps(parsed, ensure_ascii=False),
                parsed["summary_text"],
                json.dumps(parsed["win_patterns"], ensure_ascii=False),
                json.dumps(parsed["lose_patterns"], ensure_ascii=False),
                json.dumps(parsed["risk_notes"], ensure_ascii=False),
                json.dumps(parsed["improvement_suggestions"], ensure_ascii=False),
                json.dumps(parsed["next_day_hypotheses"], ensure_ascii=False),
                json.dumps(parsed["proposed_params"], ensure_ascii=False),
                parsed["confidence_score"],
            ),
        )
        row = fetch_one("SELECT id FROM llm_analysis_reports WHERE analysis_date = ? ORDER BY id DESC LIMIT 1", (analysis_date.isoformat(),))
        return int(row["id"])

    def _save_strategy_experiment(self, analysis_date: date, proposed_params: dict[str, Any]) -> dict[str, Any]:
        strategy_name = self._active_strategy()
        backtest_result = self.backtester.mini_backtest(strategy_name, proposed_params)
        adopted = self._is_adoptable(backtest_result)
        execute(
            """
            INSERT INTO strategy_experiments(
              experiment_date, strategy_name, base_params_id, proposed_params_json,
              backtest_result_json, adopted, reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                analysis_date.isoformat(),
                strategy_name,
                None,
                json.dumps(proposed_params, ensure_ascii=False),
                json.dumps(backtest_result, ensure_ascii=False),
                1 if adopted else 0,
                "LLM提案: 採用条件を満たす候補" if adopted else "LLM提案: 採用条件未達または要確認",
            ),
        )
        return backtest_result | {"adopted": adopted, "strategy_name": strategy_name}

    def _update_report_backtest(self, report_id: int, backtest_result: dict[str, Any]) -> None:
        execute(
            "UPDATE llm_analysis_reports SET backtest_result_json = ?, adopted = ? WHERE id = ?",
            (json.dumps(backtest_result, ensure_ascii=False), 1 if backtest_result.get("adopted") else 0, report_id),
        )

    def _active_strategy(self) -> str:
        row = fetch_one("SELECT value FROM app_state WHERE key = 'active_strategy'")
        value = row["value"] if row else "HybridStrategy"
        return value if value in STRATEGY_NAMES else "HybridStrategy"

    def _is_adoptable(self, result: dict[str, Any]) -> bool:
        return float(result.get("profit_rate", 0)) > 0 and float(result.get("max_drawdown", -1)) >= -0.03 and int(result.get("trade_count", 0)) >= 3

    def _row_to_report(self, row: dict[str, Any] | None) -> LlmAnalysisReport:
        if row is None:
            raise RuntimeError("LLM analysis report was not saved.")
        return LlmAnalysisReport(
            id=int(row["id"]),
            analysis_date=row["analysis_date"],
            model_name=row["model_name"],
            input_summary=json.loads(row["input_summary_json"]),
            output=json.loads(row["output_json"]),
            summary_text=row["summary_text"],
            win_patterns=json.loads(row["win_patterns"]),
            lose_patterns=json.loads(row["lose_patterns"]),
            risk_notes=json.loads(row["risk_notes"]),
            improvement_suggestions=json.loads(row["improvement_suggestions"]),
            next_day_hypotheses=json.loads(row["next_day_hypotheses"]),
            proposed_params=json.loads(row["proposed_params_json"]),
            confidence_score=float(row["confidence_score"]),
        )

    def _group_pnl(self, rows: list[dict[str, Any]], key: str) -> dict[str, float]:
        grouped: dict[str, float] = {}
        for row in rows:
            grouped[row[key]] = grouped.get(row[key], 0.0) + float(row["daily_pnl"])
        return grouped

    def _best_key(self, values: dict[str, float]) -> str | None:
        return max(values, key=values.get) if values else None

    def _worst_key(self, values: dict[str, float]) -> str | None:
        return min(values, key=values.get) if values else None
