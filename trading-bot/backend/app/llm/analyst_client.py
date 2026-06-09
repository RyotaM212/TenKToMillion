from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import get_settings
from app.llm.schemas import AnalystClientResult


class MockAnalystClient:
    model_name = "mock-analyst"

    def analyze(self, prompt: str) -> AnalystClientResult:
        output = {
            "summary_text": "本日はペーパートレード条件に合う取引が少なく、無理に入らない判断が優先されました。",
            "win_patterns": ["VWAP上で価格が維持され、出来高を伴う候補を優先する設計は継続して検証価値があります。"],
            "lose_patterns": ["候補スコアが低い日や出来高が薄い時間帯では、エントリー条件に届かず機会損失が発生しやすいです。"],
            "risk_notes": ["出来高が0または極端に少ないスナップショットは、判定材料として弱いため除外継続が妥当です。"],
            "improvement_suggestions": [
                "候補が0件の日も市場スナップショット数と除外理由を記録する",
                "エントリー開始時刻を9:15以降にして寄り付き直後のノイズを避ける検証を行う",
            ],
            "next_day_hypotheses": ["9:15以降かつVWAP上で出来高が継続する銘柄に限定すると、不要な取引を抑制できる可能性があります。"],
            "proposed_params": {
                "entry_start_time": "09:15",
                "entry_end_time": "10:20",
                "take_profit_rate": 0.12,
                "stop_loss_rate": 0.06,
                "volume_spike_threshold": 3.5,
                "breakout_threshold": 0.012,
                "vwap_exit_enabled": True,
            },
            "confidence_score": 0.62,
        }
        return AnalystClientResult(model_name=self.model_name, content=json.dumps(output, ensure_ascii=False), token_usage={"mock": True})


class OpenAIAnalystClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.openai_api_key
        self.model_name = settings.openai_analyst_model

    def analyze(self, prompt: str) -> AnalystClientResult:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured.")

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": "You return strictly valid JSON and never place trades."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
        request = Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI analyst request failed: HTTP {exc.code}: {body}") from exc
        except (URLError, TimeoutError) as exc:
            raise RuntimeError(f"OpenAI analyst request failed: {exc}") from exc

        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage") or {}
        return AnalystClientResult(model_name=self.model_name, content=content, token_usage=usage)


def build_analyst_client():
    if get_settings().openai_api_key:
        return OpenAIAnalystClient()
    return MockAnalystClient()
