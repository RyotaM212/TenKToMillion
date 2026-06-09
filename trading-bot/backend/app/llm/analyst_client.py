from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import get_settings
from app.llm.schemas import AnalystClientResult


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
    raise RuntimeError("OPENAI_API_KEY is not configured. LLM analysis requires a real OpenAI API key.")
