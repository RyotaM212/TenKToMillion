from __future__ import annotations

from abc import ABC

from app.models import MarketSnapshot, StrategyParams


class BaseStrategy(ABC):
    name = "BaseStrategy"
    minimum_score = 35.0

    def __init__(self, params: StrategyParams | None = None) -> None:
        self.params = params or StrategyParams(strategy_name=self.name)

    def adjust_score(self, snapshot: MarketSnapshot, base_score: float) -> float:
        return base_score

    def can_enter(self, snapshot: MarketSnapshot, candidate_score: float) -> bool:
        is_above_vwap = snapshot.price > snapshot.vwap
        is_breakout = snapshot.price >= snapshot.previous_close * (1 + self.params.breakout_threshold)
        is_bullish = snapshot.close > snapshot.open
        has_liquidity = snapshot.volume >= 50_000
        return is_above_vwap and is_breakout and is_bullish and has_liquidity and candidate_score >= self.minimum_score

    def describe(self, snapshot: MarketSnapshot) -> str:
        return f"{self.name}: price={snapshot.price}, volume={snapshot.volume}, vwap={snapshot.vwap}"
