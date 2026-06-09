from __future__ import annotations

import json
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.collectors.market_data_collector import MarketDataCollector
from app.config import get_settings
from app.models import MarketSnapshot


class YahooCollector(MarketDataCollector):
    def _ensure_enabled(self) -> None:
        if not get_settings().yahoo_finance_enabled:
            raise RuntimeError("Yahoo Finance collector is disabled. Enable it explicitly in local .env.")

    def fetch_symbols(self) -> list[dict[str, str]]:
        self._ensure_enabled()
        return [{"symbol": symbol, "symbol_name": f"{symbol}.T"} for symbol in get_settings().market_symbols]

    def fetch_daily_prices(self, symbol: str) -> list[MarketSnapshot]:
        self._ensure_enabled()
        return self._fetch_chart(symbol, range_value="2mo", interval="1d")

    def fetch_intraday_prices(self, symbol: str) -> list[MarketSnapshot]:
        self._ensure_enabled()
        return self._fetch_chart(symbol, range_value="1d", interval="5m")

    def fetch_ranking(self) -> list[MarketSnapshot]:
        self._ensure_enabled()
        snapshots: list[MarketSnapshot] = []
        for symbol in get_settings().market_symbols:
            try:
                prices = self.fetch_intraday_prices(symbol)
            except RuntimeError:
                continue
            if prices:
                snapshots.append(self._with_daily_volume_fallback(symbol, prices[-1]))
        if not snapshots:
            raise RuntimeError("Yahoo Finance returned no usable ranking data for configured symbols.")
        return sorted(
            snapshots,
            key=lambda item: ((item.close - item.previous_close) / max(item.previous_close, 1), item.volume),
            reverse=True,
        )

    def _with_daily_volume_fallback(self, symbol: str, snapshot: MarketSnapshot) -> MarketSnapshot:
        if snapshot.volume > 0:
            return snapshot
        try:
            daily_prices = self.fetch_daily_prices(symbol)
        except RuntimeError:
            return snapshot
        if not daily_prices:
            return snapshot
        daily = daily_prices[-1]
        return MarketSnapshot(
            symbol=snapshot.symbol,
            symbol_name=snapshot.symbol_name,
            snapshot_time=snapshot.snapshot_time,
            price=snapshot.price,
            volume=daily.volume,
            vwap=snapshot.vwap,
            open=snapshot.open,
            high=snapshot.high,
            low=snapshot.low,
            close=snapshot.close,
            previous_close=snapshot.previous_close,
            news_score=snapshot.news_score,
        )

    def _fetch_chart(self, symbol: str, range_value: str, interval: str) -> list[MarketSnapshot]:
        yahoo_symbol = symbol if symbol.endswith(".T") else f"{symbol}.T"
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}?range={range_value}&interval={interval}"
        try:
            with urlopen(Request(url, headers={"User-Agent": "TenKToMillion/0.1"}), timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError) as exc:
            raise RuntimeError(f"Yahoo Finance data fetch failed for {symbol}: {exc}") from exc

        result = (payload.get("chart", {}).get("result") or [None])[0]
        if not result:
            raise RuntimeError(f"Yahoo Finance returned no chart data for {symbol}")

        timestamps = result.get("timestamp") or []
        quote = ((result.get("indicators") or {}).get("quote") or [{}])[0]
        closes = quote.get("close") or []
        opens = quote.get("open") or []
        highs = quote.get("high") or []
        lows = quote.get("low") or []
        volumes = quote.get("volume") or []
        meta = result.get("meta") or {}
        symbol_name = meta.get("symbol", yahoo_symbol)

        snapshots: list[MarketSnapshot] = []
        previous_close = float(meta.get("chartPreviousClose") or 0)
        last_close = previous_close
        for index, timestamp in enumerate(timestamps):
            close = _number_at(closes, index)
            open_price = _number_at(opens, index)
            high = _number_at(highs, index)
            low = _number_at(lows, index)
            if close is None or open_price is None or high is None or low is None:
                continue
            volume = int(_number_at(volumes, index) or 0)
            baseline = previous_close or last_close or close
            vwap = (open_price + high + low + close) / 4
            snapshots.append(
                MarketSnapshot(
                    symbol=symbol.replace(".T", ""),
                    symbol_name=symbol_name,
                    snapshot_time=datetime.fromtimestamp(int(timestamp)),
                    price=round(close, 2),
                    volume=volume,
                    vwap=round(vwap, 2),
                    open=round(open_price, 2),
                    high=round(high, 2),
                    low=round(low, 2),
                    close=round(close, 2),
                    previous_close=round(baseline, 2),
                    news_score=0.0,
                )
            )
            last_close = close
            previous_close = close

        return snapshots


def _number_at(values: list, index: int) -> float | None:
    if index >= len(values) or values[index] is None:
        return None
    return float(values[index])
