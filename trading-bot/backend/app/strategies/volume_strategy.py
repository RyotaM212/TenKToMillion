from app.models import MarketSnapshot
from app.strategies.base_strategy import BaseStrategy


class VolumeStrategy(BaseStrategy):
    name = "VolumeStrategy"
    minimum_score = 36.0

    def adjust_score(self, snapshot: MarketSnapshot, base_score: float) -> float:
        return base_score + min(snapshot.volume / 120_000, 15)
