from app.models import Candidate, MarketSnapshot


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
