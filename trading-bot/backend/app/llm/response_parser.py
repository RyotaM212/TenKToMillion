from __future__ import annotations

import json
from typing import Any


REQUIRED_FIELDS = (
    "summary_text",
    "win_patterns",
    "lose_patterns",
    "risk_notes",
    "improvement_suggestions",
    "next_day_hypotheses",
    "proposed_params",
    "confidence_score",
)

DANGEROUS_OUTPUT_PATTERNS = (
    "信用取引を使",
    "信用取引を利用",
    "信用で買",
    "空売りを使",
    "空売りを利用",
    "ショートを使",
    "ショートを利用",
    "レバレッジを使",
    "レバレッジを利用",
    "証券APIで発注",
    "実売買を有効",
    "実売買で発注",
    "自動発注",
    "発注する",
    "注文を出す",
    "RiskGuardを無効",
    "ナンピンする",
    "ナンピンを許可",
    "持ち越しする",
    "持ち越しを許可",
)


class ResponseParser:
    def parse(self, raw_content: str) -> dict[str, Any]:
        content = raw_content.strip()
        if content.startswith("```"):
            content = content.strip("`")
            if content.startswith("json"):
                content = content[4:].strip()

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(f"LLM output is not valid JSON: {exc}") from exc

        if not isinstance(parsed, dict):
            raise ValueError("LLM output must be a JSON object.")

        missing = [field for field in REQUIRED_FIELDS if field not in parsed]
        if missing:
            raise ValueError(f"LLM output is missing fields: {', '.join(missing)}")

        for key in ("win_patterns", "lose_patterns", "risk_notes", "improvement_suggestions", "next_day_hypotheses"):
            if not isinstance(parsed[key], list) or not all(isinstance(item, str) for item in parsed[key]):
                raise ValueError(f"{key} must be a list of strings.")

        if not isinstance(parsed["summary_text"], str):
            raise ValueError("summary_text must be a string.")
        if not isinstance(parsed["proposed_params"], dict):
            raise ValueError("proposed_params must be an object.")

        confidence = float(parsed["confidence_score"])
        if confidence < 0 or confidence > 1:
            raise ValueError("confidence_score must be between 0 and 1.")
        parsed["confidence_score"] = confidence

        output_text = json.dumps(parsed, ensure_ascii=False)
        if any(pattern in output_text for pattern in DANGEROUS_OUTPUT_PATTERNS):
            raise ValueError("LLM output contains forbidden trading or risk-control instructions.")

        return parsed
