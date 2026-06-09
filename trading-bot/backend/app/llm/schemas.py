from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LlmAnalysisReport:
    id: int
    analysis_date: str
    model_name: str
    input_summary: dict[str, Any]
    output: dict[str, Any]
    summary_text: str
    win_patterns: list[str]
    lose_patterns: list[str]
    risk_notes: list[str]
    improvement_suggestions: list[str]
    next_day_hypotheses: list[str]
    proposed_params: dict[str, Any]
    confidence_score: float


@dataclass(frozen=True)
class AnalystClientResult:
    model_name: str
    content: str
    token_usage: dict[str, Any]
