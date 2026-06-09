from app.strategies.base_strategy import BaseStrategy
from app.strategies.hybrid_strategy import HybridStrategy
from app.strategies.momentum_strategy import MomentumStrategy
from app.strategies.news_strategy import NewsStrategy
from app.strategies.volume_strategy import VolumeStrategy


def build_strategies() -> list[BaseStrategy]:
    return [VolumeStrategy(), MomentumStrategy(), NewsStrategy(), HybridStrategy()]
