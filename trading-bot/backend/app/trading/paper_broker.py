from __future__ import annotations

from datetime import date

from app.db import execute
from app.models import Candidate, MarketSnapshot, StrategyParams
from app.trading.capital_manager import CapitalManager
from app.trading.risk_guard import RiskGuard


class PaperBroker:
    def __init__(self, initial_cash: float, persist: bool = True) -> None:
        self.capital_manager = CapitalManager(initial_cash)
        self.risk_guard = RiskGuard()
        self.persist = persist

    def run_for_candidate(
        self,
        mode: str,
        candidate: Candidate,
        snapshot: MarketSnapshot,
        params: StrategyParams,
        realized_pnl: float,
        locked_profit: float,
        already_traded_today: bool,
    ) -> dict[str, float | str | int] | None:
        if mode == "ONE_SHOT_MODE" and already_traded_today:
            return None

        ok, reason = self.risk_guard.validate_entry(candidate, snapshot, open_positions=0)
        if not ok:
            return None

        cash = self.capital_manager.buying_power(mode, realized_pnl, locked_profit)
        quantity = self.capital_manager.quantity_for(cash, snapshot.price)
        if quantity < 1:
            return None

        simulated_exit = self._simulate_exit(snapshot, params)
        pnl = round((simulated_exit["exit_price"] - snapshot.price) * quantity, 2)
        pnl_rate = round((simulated_exit["exit_price"] - snapshot.price) / snapshot.price, 4)
        if self.persist:
            execute(
                """
                INSERT INTO paper_trades(
                  trade_date, mode, strategy_name, symbol, symbol_name, entry_time, entry_price,
                  exit_time, exit_price, quantity, pnl, pnl_rate, exit_reason, candidate_score,
                  entry_reason, max_unrealized_profit, max_unrealized_loss
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    date.today().isoformat(),
                    mode,
                    candidate.strategy_name,
                    candidate.symbol,
                    candidate.symbol_name,
                    snapshot.snapshot_time.isoformat(),
                    snapshot.price,
                    simulated_exit["exit_time"],
                    simulated_exit["exit_price"],
                    quantity,
                    pnl,
                    pnl_rate,
                    simulated_exit["exit_reason"],
                    candidate.score,
                    reason,
                    max(0, round((snapshot.high - snapshot.price) * quantity, 2)),
                    min(0, round((snapshot.low - snapshot.price) * quantity, 2)),
                ),
            )
        return {"pnl": pnl, "locked_profit": self.capital_manager.locked_profit_after_trade(mode, locked_profit, pnl)}

    def _simulate_exit(self, snapshot: MarketSnapshot, params: StrategyParams) -> dict[str, float | str]:
        take_profit = snapshot.price * (1 + params.take_profit_rate)
        stop_loss = snapshot.price * (1 - params.stop_loss_rate)
        if snapshot.high >= take_profit:
            return {"exit_price": round(take_profit, 2), "exit_reason": "利確", "exit_time": "10:15"}
        if snapshot.low <= stop_loss:
            return {"exit_price": round(stop_loss, 2), "exit_reason": "損切", "exit_time": "10:20"}
        if params.vwap_exit_enabled and snapshot.close < snapshot.vwap:
            return {"exit_price": snapshot.close, "exit_reason": "VWAP割れ", "exit_time": "11:00"}
        if snapshot.close >= snapshot.open:
            exit_price = min(snapshot.high, snapshot.price * 1.03)
        else:
            exit_price = max(snapshot.low, snapshot.price * 0.98)
        return {"exit_price": round(exit_price, 2), "exit_reason": "14:45強制決済", "exit_time": "14:45"}
