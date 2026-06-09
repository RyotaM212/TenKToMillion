from datetime import date

from app.models import Candidate, MarketSnapshot
from app.screening.scoring import score_snapshot
from app.strategies.base_strategy import BaseStrategy


class UniverseFilter:
    def build_candidates(self, snapshots: list[MarketSnapshot], strategy: BaseStrategy) -> list[Candidate]:
        candidates: list[Candidate] = []
        for snapshot in snapshots:
            scores = score_snapshot(snapshot)
            strategy_score = strategy.adjust_score(snapshot, scores["score"])
            if strategy_score < strategy.minimum_score:
                continue
            candidates.append(
                Candidate(
                    trade_date=date.today().isoformat(),
                    symbol=snapshot.symbol,
                    symbol_name=snapshot.symbol_name,
                    score=round(strategy_score, 2),
                    strategy_name=strategy.name,
                    volume_spike_score=scores["volume_spike_score"],
                    price_change_score=scores["price_change_score"],
                    gap_up_score=scores["gap_up_score"],
                    volatility_score=scores["volatility_score"],
                    news_score=scores["news_score"],
                    liquidity_score=scores["liquidity_score"],
                    selected_reason=strategy.describe(snapshot),
                )
            )
        return sorted(candidates, key=lambda item: item.score, reverse=True)
