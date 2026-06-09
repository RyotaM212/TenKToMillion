from __future__ import annotations

from datetime import datetime

from app.analysis.strategy_params_repository import normalize_strategy_params, params_to_json
from app.db import fetch_all
from app.models import Candidate, MarketSnapshot
from app.strategies import build_strategies
from app.trading.paper_broker import PaperBroker


class Backtester:
    def mini_backtest(self, strategy_name: str, proposed_params: dict[str, float | str | bool]) -> dict[str, float | str]:
        params = normalize_strategy_params(strategy_name, proposed_params)
        strategy = next((item for item in build_strategies() if item.name == strategy_name), None)
        if strategy is None:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        strategy.params = params

        snapshots = self._snapshots_by_symbol()
        candidates = self._candidates(strategy_name)
        broker = PaperBroker(initial_cash=10_000, persist=False)
        pnl_values: list[float] = []
        realized_pnl = 0.0
        locked_profit = 0.0
        already_traded = False
        for candidate in candidates:
            snapshot = snapshots.get(candidate.symbol)
            if not snapshot or not strategy.can_enter(snapshot, candidate.score):
                continue
            result = broker.run_for_candidate("YOLO_MODE", candidate, snapshot, params, realized_pnl, locked_profit, already_traded)
            if not result:
                continue
            pnl = float(result["pnl"])
            pnl_values.append(pnl)
            realized_pnl += pnl
            locked_profit = float(result["locked_profit"])
            already_traded = True

        total_pnl = round(sum(pnl_values), 2)
        trade_count = len(pnl_values)
        max_drawdown = self._max_drawdown(pnl_values)
        return {
            "strategy_name": strategy_name,
            "profit_rate": round(total_pnl / 10_000, 4),
            "max_drawdown": max_drawdown,
            "trade_count": trade_count,
            "note": "Replay backtest using stored candidates and market snapshots.",
            "params": params_to_json(params),
        }

    def _snapshots_by_symbol(self) -> dict[str, MarketSnapshot]:
        rows = fetch_all("SELECT * FROM market_snapshots ORDER BY created_at DESC, id DESC LIMIT 500")
        snapshots: dict[str, MarketSnapshot] = {}
        for row in rows:
            symbol = str(row["symbol"])
            if symbol in snapshots:
                continue
            snapshots[symbol] = MarketSnapshot(
                symbol=symbol,
                symbol_name=str(row["symbol_name"]),
                snapshot_time=datetime.fromisoformat(str(row["snapshot_time"])),
                price=float(row["price"]),
                volume=int(row["volume"]),
                vwap=float(row["vwap"]),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                previous_close=float(row["previous_close"]),
                news_score=float(row["news_score"]),
            )
        return snapshots

    def _candidates(self, strategy_name: str) -> list[Candidate]:
        rows = fetch_all("SELECT * FROM candidates WHERE strategy_name = ? ORDER BY trade_date DESC, score DESC LIMIT 100", (strategy_name,))
        return [
            Candidate(
                trade_date=str(row["trade_date"]),
                symbol=str(row["symbol"]),
                symbol_name=str(row["symbol_name"]),
                score=float(row["score"]),
                strategy_name=str(row["strategy_name"]),
                volume_spike_score=float(row["volume_spike_score"]),
                price_change_score=float(row["price_change_score"]),
                gap_up_score=float(row["gap_up_score"]),
                volatility_score=float(row["volatility_score"]),
                news_score=float(row["news_score"]),
                liquidity_score=float(row["liquidity_score"]),
                selected_reason=str(row["selected_reason"]),
            )
            for row in rows
        ]

    def _max_drawdown(self, pnl_values: list[float]) -> float:
        equity = 0.0
        peak = 0.0
        max_drawdown = 0.0
        for pnl in pnl_values:
            equity += pnl
            peak = max(peak, equity)
            max_drawdown = min(max_drawdown, equity - peak)
        return round(max_drawdown / 10_000, 4)
