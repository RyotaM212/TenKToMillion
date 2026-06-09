from __future__ import annotations

import json
from typing import Any

from app.config import get_settings
from app.db import fetch_all


JPY_PER_USD = 157.0

MODEL_PRICING_USD_PER_1M = {
    "gpt-4.1-mini": {"input": 0.40, "cached_input": 0.10, "output": 1.60},
    "gpt-4.1": {"input": 2.00, "cached_input": 0.50, "output": 8.00},
    "gpt-4.1-nano": {"input": 0.10, "cached_input": 0.025, "output": 0.40},
    "gpt-5-mini": {"input": 0.25, "cached_input": 0.025, "output": 2.00},
    "gpt-5-nano": {"input": 0.05, "cached_input": 0.005, "output": 0.40},
}


class OpenAICostService:
    def history(self) -> dict[str, Any]:
        rows = fetch_all(
            """
            SELECT
              runs.*,
              COALESCE(
                (
                  SELECT reports.model_name
                  FROM llm_analysis_reports reports
                  WHERE reports.analysis_date = runs.analysis_date
                    AND reports.created_at >= runs.created_at
                  ORDER BY reports.created_at ASC
                  LIMIT 1
                ),
                ?
              ) AS model_name
            FROM llm_analysis_runs runs
            ORDER BY runs.created_at DESC
            LIMIT 50
            """,
            (get_settings().openai_analyst_model,),
        )
        items = [self._row_to_item(row) for row in rows]
        total_usd = sum(item["estimated_cost_usd"] for item in items)
        total_tokens = sum(item["total_tokens"] for item in items)
        return {
            "items": items,
            "total_estimated_cost_usd": round(total_usd, 6),
            "total_estimated_cost_jpy": round(total_usd * JPY_PER_USD, 2),
            "total_tokens": total_tokens,
            "currency_note": f"概算表示。1 USD = {JPY_PER_USD:.0f} JPYで換算。",
        }

    def _row_to_item(self, row: dict[str, Any]) -> dict[str, Any]:
        usage = _safe_json(row["token_usage_json"])
        model_name = str(row["model_name"])
        pricing = MODEL_PRICING_USD_PER_1M.get(model_name, MODEL_PRICING_USD_PER_1M["gpt-4.1-mini"])
        prompt_tokens = int(usage.get("prompt_tokens") or 0)
        completion_tokens = int(usage.get("completion_tokens") or 0)
        total_tokens = int(usage.get("total_tokens") or prompt_tokens + completion_tokens)
        cached_tokens = int((usage.get("prompt_tokens_details") or {}).get("cached_tokens") or 0)
        billable_input_tokens = max(prompt_tokens - cached_tokens, 0)
        estimated_cost_usd = (
            billable_input_tokens * pricing["input"]
            + cached_tokens * pricing["cached_input"]
            + completion_tokens * pricing["output"]
        ) / 1_000_000
        return {
            "id": int(row["id"]),
            "analysis_date": row["analysis_date"],
            "status": row["status"],
            "model_name": model_name,
            "started_at": row["started_at"],
            "finished_at": row["finished_at"],
            "prompt_tokens": prompt_tokens,
            "cached_prompt_tokens": cached_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": round(estimated_cost_usd, 6),
            "estimated_cost_jpy": round(estimated_cost_usd * JPY_PER_USD, 2),
            "error_message": row["error_message"],
        }


def _safe_json(raw: str) -> dict[str, Any]:
    try:
        parsed = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}
