from abc import ABC, abstractmethod

from app.models import MarketSnapshot


class MarketDataCollector(ABC):
    @abstractmethod
    def fetch_symbols(self) -> list[dict[str, str]]:
        raise NotImplementedError

    @abstractmethod
    def fetch_daily_prices(self, symbol: str) -> list[MarketSnapshot]:
        raise NotImplementedError

    @abstractmethod
    def fetch_intraday_prices(self, symbol: str) -> list[MarketSnapshot]:
        raise NotImplementedError

    @abstractmethod
    def fetch_ranking(self) -> list[MarketSnapshot]:
        raise NotImplementedError
