from app.models import MarketSnapshot
from app.strategies.base_strategy import BaseStrategy


class MomentumStrategy(BaseStrategy):
    name = "MomentumStrategy"
    minimum_score = 38.0

    def adjust_score(self, snapshot: MarketSnapshot, base_score: float) -> float:
        momentum = (snapshot.close - snapshot.previous_close) / snapshot.previous_close
        return base_score + max(0, momentum * 120)
