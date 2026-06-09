from app.strategies.base_strategy import BaseStrategy
from app.strategies.hybrid_strategy import HybridStrategy
from app.strategies.momentum_strategy import MomentumStrategy
from app.strategies.news_strategy import NewsStrategy
from app.strategies.volume_strategy import VolumeStrategy


def build_strategies() -> list[BaseStrategy]:
    from app.analysis.strategy_params_repository import latest_params_for_all

    params = latest_params_for_all()
    return [
        VolumeStrategy(params["VolumeStrategy"]),
        MomentumStrategy(params["MomentumStrategy"]),
        NewsStrategy(params["NewsStrategy"]),
        HybridStrategy(params["HybridStrategy"]),
    ]
