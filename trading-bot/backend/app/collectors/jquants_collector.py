from __future__ import annotations

import json
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.collectors.market_data_collector import MarketDataCollector
from app.config import get_settings
from app.models import MarketSnapshot


class JQuantsCollector(MarketDataCollector):
    base_url = "https://api.jquants.com/v1"

    def __init__(self) -> None:
        self._id_token: str | None = None
        self._listed_names: dict[str, str] | None = None

    def _ensure_configured(self) -> None:
        settings = get_settings()
        if not settings.jquants_email or not settings.jquants_password:
            raise RuntimeError("J-Quants credentials are not configured. Set them via local .env or GitHub Secrets.")

    def fetch_symbols(self) -> list[dict[str, str]]:
        self._ensure_configured()
        names = self._fetch_listed_names()
        return [{"symbol": symbol, "symbol_name": names.get(symbol, symbol)} for symbol in get_settings().market_symbols]

    def fetch_daily_prices(self, symbol: str) -> list[MarketSnapshot]:
        self._ensure_configured()
        payload = self._request_json("GET", f"/prices/daily_quotes?{urlencode({'code': symbol})}")
        quotes = payload.get("daily_quotes") or []
        names = self._fetch_listed_names()
        snapshots = [self._quote_to_snapshot(quote, names.get(symbol, symbol)) for quote in quotes]
        return [snapshot for snapshot in snapshots if snapshot is not None]

    def fetch_intraday_prices(self, symbol: str) -> list[MarketSnapshot]:
        self._ensure_configured()
        return self.fetch_daily_prices(symbol)

    def fetch_ranking(self) -> list[MarketSnapshot]:
        self._ensure_configured()
        snapshots: list[MarketSnapshot] = []
        for symbol in get_settings().market_symbols:
            try:
                prices = self.fetch_daily_prices(symbol)
            except RuntimeError:
                continue
            if prices:
                snapshots.append(prices[-1])
        if not snapshots:
            raise RuntimeError("J-Quants returned no usable ranking data for configured symbols.")
        return sorted(
            snapshots,
            key=lambda item: ((item.close - item.previous_close) / max(item.previous_close, 1), item.volume),
            reverse=True,
        )

    def _fetch_listed_names(self) -> dict[str, str]:
        if self._listed_names is not None:
            return self._listed_names
        payload = self._request_json("GET", "/listed/info")
        rows = payload.get("info") or []
        self._listed_names = {
            str(row.get("Code", "")).strip(): str(row.get("CompanyName") or row.get("CompanyNameEnglish") or row.get("Code") or "").strip()
            for row in rows
            if row.get("Code")
        }
        return self._listed_names

    def _quote_to_snapshot(self, quote: dict, symbol_name: str) -> MarketSnapshot | None:
        symbol = str(quote.get("Code") or "").strip()
        close = _as_float(quote.get("AdjustmentClose") or quote.get("Close"))
        open_price = _as_float(quote.get("AdjustmentOpen") or quote.get("Open"))
        high = _as_float(quote.get("AdjustmentHigh") or quote.get("High"))
        low = _as_float(quote.get("AdjustmentLow") or quote.get("Low"))
        previous_close = _as_float(quote.get("AdjustmentPreviousClose") or quote.get("PreviousClose"))
        if not symbol or close is None or open_price is None or high is None or low is None:
            return None
        volume = int(_as_float(quote.get("AdjustmentVolume") or quote.get("Volume")) or 0)
        date_text = str(quote.get("Date") or datetime.now().date().isoformat())
        baseline = previous_close or open_price
        return MarketSnapshot(
            symbol=symbol,
            symbol_name=symbol_name,
            snapshot_time=datetime.fromisoformat(date_text),
            price=round(close, 2),
            volume=volume,
            vwap=round((open_price + high + low + close) / 4, 2),
            open=round(open_price, 2),
            high=round(high, 2),
            low=round(low, 2),
            close=round(close, 2),
            previous_close=round(baseline, 2),
            news_score=0.0,
        )

    def _request_json(self, method: str, path: str, body: dict | None = None) -> dict:
        is_auth_endpoint = path.startswith("/token/auth_user") or path.startswith("/token/auth_refresh")
        if not is_auth_endpoint and self._id_token is None:
            self._id_token = self._fetch_id_token()
        headers = {"Content-Type": "application/json"}
        if self._id_token:
            headers["Authorization"] = f"Bearer {self._id_token}"
        data = json.dumps(body).encode("utf-8") if body is not None else None
        try:
            with urlopen(Request(f"{self.base_url}{path}", data=data, headers=headers, method=method), timeout=15) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError) as exc:
            raise RuntimeError(f"J-Quants API request failed: {path}: {exc}") from exc

    def _fetch_id_token(self) -> str:
        settings = get_settings()
        auth = self._request_json(
            "POST",
            "/token/auth_user",
            {"mailaddress": settings.jquants_email, "password": settings.jquants_password},
        )
        refresh_token = auth.get("refreshToken")
        if not refresh_token:
            raise RuntimeError("J-Quants refresh token was not returned.")
        token = self._request_json("POST", f"/token/auth_refresh?{urlencode({'refreshtoken': refresh_token})}")
        id_token = token.get("idToken")
        if not id_token:
            raise RuntimeError("J-Quants ID token was not returned.")
        return str(id_token)


def _as_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    return float(value)
