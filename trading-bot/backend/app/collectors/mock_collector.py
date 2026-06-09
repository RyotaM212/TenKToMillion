from datetime import datetime, timedelta
from random import Random

from app.collectors.market_data_collector import MarketDataCollector
from app.models import MarketSnapshot


class MockCollector(MarketDataCollector):
    def __init__(self, seed: int = 10_000) -> None:
        self.random = Random(seed)
        self.symbols = [
            ("3778", "さくらインターネット"),
            ("2160", "ジーエヌアイ"),
            ("4565", "そーせい"),
            ("6920", "レーザーテック"),
            ("5253", "カバー"),
            ("7014", "名村造船所"),
            ("1514", "住石HD"),
            ("5586", "Laboro.AI"),
            ("5595", "QPS研究所"),
            ("6526", "ソシオネクスト"),
        ]

    def fetch_symbols(self) -> list[dict[str, str]]:
        return [{"symbol": symbol, "symbol_name": name} for symbol, name in self.symbols]

    def fetch_daily_prices(self, symbol: str) -> list[MarketSnapshot]:
        return self._build_snapshots(symbol, count=20, minute_step=1440)

    def fetch_intraday_prices(self, symbol: str) -> list[MarketSnapshot]:
        return self._build_snapshots(symbol, count=24, minute_step=5)

    def fetch_ranking(self) -> list[MarketSnapshot]:
        return [self._build_snapshots(symbol, count=1, minute_step=5)[0] for symbol, _ in self.symbols]

    def _build_snapshots(self, symbol: str, count: int, minute_step: int) -> list[MarketSnapshot]:
        symbol_name = dict(self.symbols).get(symbol, symbol)
        base = self.random.randint(90, 950)
        previous_close = float(base)
        start = datetime.now().replace(hour=9, minute=5, second=0, microsecond=0)
        snapshots: list[MarketSnapshot] = []
        last_close = previous_close

        for index in range(count):
            drift = 1 + self.random.uniform(-0.025, 0.055)
            open_price = max(1, last_close * (1 + self.random.uniform(-0.01, 0.02)))
            close = max(1, open_price * drift)
            high = max(open_price, close) * (1 + self.random.uniform(0.003, 0.03))
            low = min(open_price, close) * (1 - self.random.uniform(0.003, 0.025))
            volume = self.random.randint(40_000, 1_800_000)
            vwap = (open_price + high + low + close) / 4
            snapshots.append(
                MarketSnapshot(
                    symbol=symbol,
                    symbol_name=symbol_name,
                    snapshot_time=start + timedelta(minutes=index * minute_step),
                    price=round(close, 2),
                    volume=volume,
                    vwap=round(vwap, 2),
                    open=round(open_price, 2),
                    high=round(high, 2),
                    low=round(low, 2),
                    close=round(close, 2),
                    previous_close=round(previous_close, 2),
                    news_score=round(self.random.uniform(0, 1), 3),
                )
            )
            last_close = close

        return snapshots
