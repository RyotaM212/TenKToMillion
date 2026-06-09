from __future__ import annotations

from typing import Any

from app.collectors.jquants_collector import JQuantsCollector
from app.collectors.market_data_collector import MarketDataCollector
from app.collectors.yahoo_collector import YahooCollector
from app.models import Candidate, MarketSnapshot
from app.screening.universe_filter import UniverseFilter
from app.strategies import build_strategies


class DataSourceComparison:
    def compare(self) -> dict[str, Any]:
        sources = {
            "jquants": JQuantsCollector(),
            "yahoo": YahooCollector(),
        }
        results = {name: self._source_result(name, collector) for name, collector in sources.items()}
        return {
            "sources": results,
            "overlap_symbols": self._overlap_symbols(results),
            "summary": self._summary(results),
        }

    def _source_result(self, name: str, collector: MarketDataCollector) -> dict[str, Any]:
        try:
            snapshots = collector.fetch_ranking()
            candidates = self._build_candidates(snapshots)
            return {
                "source": name,
                "status": "success",
                "snapshot_count": len(snapshots),
                "candidate_count": len(candidates),
                "top_candidates": [self._candidate_to_dict(candidate) for candidate in candidates[:10]],
                "top_snapshots": [self._snapshot_to_dict(snapshot) for snapshot in snapshots[:10]],
                "error_message": None,
            }
        except RuntimeError as exc:
            return {
                "source": name,
                "status": "failed",
                "snapshot_count": 0,
                "candidate_count": 0,
                "top_candidates": [],
                "top_snapshots": [],
                "error_message": str(exc),
            }

    def _build_candidates(self, snapshots: list[MarketSnapshot]) -> list[Candidate]:
        universe_filter = UniverseFilter()
        candidates: list[Candidate] = []
        for strategy in build_strategies():
            candidates.extend(universe_filter.build_candidates(snapshots, strategy)[:20])
        return sorted(candidates, key=lambda item: item.score, reverse=True)

    def _overlap_symbols(self, results: dict[str, dict[str, Any]]) -> list[str]:
        symbol_sets = [
            {candidate["symbol"] for candidate in result["top_candidates"]}
            for result in results.values()
            if result["status"] == "success"
        ]
        if len(symbol_sets) < 2:
            return []
        return sorted(set.intersection(*symbol_sets))

    def _summary(self, results: dict[str, dict[str, Any]]) -> str:
        successful = [result for result in results.values() if result["status"] == "success"]
        if len(successful) == 2:
            return "J-QuantsとYahoo系の候補を同じスコアリングで比較しました。差分はデータ粒度と取得タイミングの違いとして扱ってください。"
        if successful:
            return "片方のデータソースのみ取得できました。失敗側の設定または外部API状態を確認してください。"
        return "両方のデータソース取得に失敗しました。ネットワーク、APIキー、Yahoo系有効化設定を確認してください。"

    def _candidate_to_dict(self, candidate: Candidate) -> dict[str, Any]:
        return {
            "symbol": candidate.symbol,
            "symbol_name": candidate.symbol_name,
            "strategy_name": candidate.strategy_name,
            "score": candidate.score,
            "selected_reason": candidate.selected_reason,
        }

    def _snapshot_to_dict(self, snapshot: MarketSnapshot) -> dict[str, Any]:
        return {
            "symbol": snapshot.symbol,
            "symbol_name": snapshot.symbol_name,
            "snapshot_time": snapshot.snapshot_time.isoformat(),
            "price": snapshot.price,
            "volume": snapshot.volume,
            "vwap": snapshot.vwap,
            "previous_close": snapshot.previous_close,
        }
