from __future__ import annotations

import json


class PromptBuilder:
    def build_daily_analysis_prompt(self, payload: dict) -> str:
        input_json = json.dumps(payload, ensure_ascii=False, indent=2)
        return f"""
あなたはトレードBotの分析担当です。
あなたは売買注文を出してはいけません。
あなたは投資助言者ではなく、ログ分析者です。
入力されたペーパートレード結果を分析し、改善提案をJSONで返してください。
信用取引・空売り・レバレッジを提案してはいけません。
RiskGuardを無効化する提案、現物以外の取引、持ち越し、ナンピンを提案してはいけません。
出力は必ず指定JSON形式にしてください。Markdownや説明文をJSONの外に出してはいけません。

出力JSON形式:
{{
  "summary_text": "string",
  "win_patterns": ["string"],
  "lose_patterns": ["string"],
  "risk_notes": ["string"],
  "improvement_suggestions": ["string"],
  "next_day_hypotheses": ["string"],
  "proposed_params": {{
    "entry_start_time": "HH:MM",
    "entry_end_time": "HH:MM",
    "take_profit_rate": 0.12,
    "stop_loss_rate": 0.06,
    "volume_spike_threshold": 4.0,
    "breakout_threshold": 0.012,
    "vwap_exit_enabled": true
  }},
  "confidence_score": 0.0
}}

入力JSON:
{input_json}
""".strip()
