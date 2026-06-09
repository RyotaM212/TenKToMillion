from typing import Any

from app.models import Candidate, MarketSnapshot, OrderRequest


class RiskGuard:
    def validate_entry(self, candidate: Candidate, snapshot: MarketSnapshot, open_positions: int) -> tuple[bool, str]:
        if open_positions >= 1:
            return False, "同時保有は1銘柄まで"
        if snapshot.price <= 0:
            return False, "価格が不正"
        if snapshot.volume < 50_000:
            return False, "流動性不足"
        if snapshot.price > 10_000:
            return False, "初期資金に対して単価が高すぎる"
        if candidate.score < 34:
            return False, "候補スコア不足"
        return True, "risk checks passed"

    def validate_order(self, order: OrderRequest, account_state: dict[str, Any], positions: list[dict[str, Any]]) -> tuple[bool, str]:
        if order.order_type != "cash":
            return False, "現物注文以外は禁止"
        if order.leverage != 1.0:
            return False, "レバレッジは禁止"
        if order.side not in ("buy", "sell"):
            return False, "注文方向が不正"
        if order.side == "sell" and not self._has_position(order.symbol, positions):
            return False, "空売りは禁止"
        if order.quantity <= 0 or order.price <= 0:
            return False, "数量または価格が不正"
        if order.side == "buy" and self._has_position(order.symbol, positions):
            return False, "ナンピンは禁止"
        if order.side == "buy" and len(positions) >= 1:
            return False, "同時保有は1銘柄まで"
        if order.side == "buy" and order.price * order.quantity > float(account_state.get("cash", 0)):
            return False, "資金以上の注文は禁止"
        if order.allow_overnight:
            return False, "持ち越しは禁止"
        if order.is_averaging_down:
            return False, "ナンピンは禁止"
        return True, "order risk checks passed"

    def _has_position(self, symbol: str, positions: list[dict[str, Any]]) -> bool:
        return any(str(position.get("symbol")) == symbol and int(position.get("quantity", 0)) > 0 for position in positions)
