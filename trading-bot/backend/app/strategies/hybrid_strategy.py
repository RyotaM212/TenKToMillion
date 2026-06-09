from app.models import MarketSnapshot
from app.strategies.base_strategy import BaseStrategy


class HybridStrategy(BaseStrategy):
    name = "HybridStrategy"
    minimum_score = 40.0

    def adjust_score(self, snapshot: MarketSnapshot, base_score: float) -> float:
        momentum = max(0, (snapshot.close - snapshot.previous_close) / snapshot.previous_close)
        liquidity = min(snapshot.volume / 500_000, 1)
        return base_score + momentum * 80 + snapshot.news_score * 8 + liquidity * 8
