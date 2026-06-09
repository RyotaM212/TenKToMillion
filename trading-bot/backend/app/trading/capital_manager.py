from app.models import CAPITAL_MODES


class CapitalManager:
    def __init__(self, initial_cash: float) -> None:
        self.initial_cash = initial_cash

    def buying_power(self, mode: str, realized_pnl: float, locked_profit: float) -> float:
        if mode not in CAPITAL_MODES:
            raise ValueError(f"Unknown capital mode: {mode}")
        if mode == "LOCK_PROFIT_MODE":
            return max(0, self.initial_cash + realized_pnl - locked_profit)
        return max(0, self.initial_cash + realized_pnl)

    def locked_profit_after_trade(self, mode: str, previous_locked: float, pnl: float) -> float:
        if mode == "LOCK_PROFIT_MODE" and pnl > 0:
            return previous_locked + pnl * 0.5
        return previous_locked

    def quantity_for(self, cash: float, price: float) -> int:
        if price <= 0:
            return 0
        return max(0, int(cash // price))
