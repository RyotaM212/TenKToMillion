from app.models import MarketSnapshot
from app.strategies.base_strategy import BaseStrategy


class NewsStrategy(BaseStrategy):
    name = "NewsStrategy"
    minimum_score = 34.0

    def adjust_score(self, snapshot: MarketSnapshot, base_score: float) -> float:
        return base_score + snapshot.news_score * 18
