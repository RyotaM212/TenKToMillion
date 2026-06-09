from datetime import date
from datetime import datetime

from app.collectors.market_data_collector import MarketDataCollector
from app.db import execute, fetch_all
from app.models import CAPITAL_MODES, Candidate, MarketSnapshot, StrategyParams
from app.strategies import build_strategies
from app.trading.paper_broker import PaperBroker


class ExecutionEngine:
    def __init__(self, collector: MarketDataCollector, initial_cash: float) -> None:
        self.collector = collector
        self.paper_broker = PaperBroker(initial_cash)

    def run_paper_trades(self) -> dict[str, int]:
        execute("DELETE FROM paper_trades WHERE trade_date = ?", (date.today().isoformat(),))
        snapshots = self._latest_snapshots_by_symbol()
        if not snapshots:
            snapshots = {snapshot.symbol: snapshot for snapshot in self.collector.fetch_ranking()}
        trades_before = fetch_all("SELECT id FROM paper_trades")
        for mode in CAPITAL_MODES:
            for strategy in build_strategies():
                candidates = fetch_all(
                    """
                    SELECT * FROM candidates
                    WHERE strategy_name = ?
                    ORDER BY score DESC
                    LIMIT 5
                    """,
                    (strategy.name,),
                )
                realized_pnl = 0.0
                locked_profit = 0.0
                already_traded = False
                for row in candidates:
                    snapshot = snapshots.get(row["symbol"])
                    if not snapshot:
                        continue
                    candidate = Candidate(
                        trade_date=row["trade_date"],
                        symbol=row["symbol"],
                        symbol_name=row["symbol_name"],
                        score=row["score"],
                        strategy_name=row["strategy_name"],
                        volume_spike_score=row["volume_spike_score"],
                        price_change_score=row["price_change_score"],
                        gap_up_score=row["gap_up_score"],
                        volatility_score=row["volatility_score"],
                        news_score=row["news_score"],
                        liquidity_score=row["liquidity_score"],
                        selected_reason=row["selected_reason"],
                    )
                    if not strategy.can_enter(snapshot, candidate.score):
                        continue
                    result = self.paper_broker.run_for_candidate(
                        mode,
                        candidate,
                        snapshot,
                        StrategyParams(strategy_name=strategy.name),
                        realized_pnl,
                        locked_profit,
                        already_traded,
                    )
                    if result:
                        realized_pnl += float(result["pnl"])
                        locked_profit = float(result["locked_profit"])
                        already_traded = True
                        break

        trades_after = fetch_all("SELECT id FROM paper_trades")
        execute("DELETE FROM paper_positions")
        return {"created": len(trades_after) - len(trades_before)}

    def _latest_snapshots_by_symbol(self) -> dict[str, MarketSnapshot]:
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
