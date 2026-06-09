from dataclasses import dataclass
from datetime import datetime
from typing import Literal


CAPITAL_MODES = ("YOLO_MODE", "LOCK_PROFIT_MODE", "ONE_SHOT_MODE")
STRATEGY_NAMES = ("VolumeStrategy", "MomentumStrategy", "NewsStrategy", "HybridStrategy")


@dataclass(frozen=True)
class MarketSnapshot:
    symbol: str
    symbol_name: str
    snapshot_time: datetime
    price: float
    volume: int
    vwap: float
    open: float
    high: float
    low: float
    close: float
    previous_close: float
    news_score: float


@dataclass(frozen=True)
class Candidate:
    trade_date: str
    symbol: str
    symbol_name: str
    score: float
    strategy_name: str
    volume_spike_score: float
    price_change_score: float
    gap_up_score: float
    volatility_score: float
    news_score: float
    liquidity_score: float
    selected_reason: str


@dataclass(frozen=True)
class StrategyParams:
    strategy_name: str
    take_profit_rate: float = 0.15
    stop_loss_rate: float = 0.08
    entry_start_time: str = "09:10"
    entry_end_time: str = "10:30"
    volume_spike_threshold: float = 3.0
    breakout_threshold: float = 0.01
    vwap_exit_enabled: bool = True


@dataclass(frozen=True)
class OrderRequest:
    side: Literal["buy", "sell"]
    symbol: str
    quantity: int
    price: float
    order_type: Literal["cash"] = "cash"
    leverage: float = 1.0
    allow_overnight: bool = False
    is_averaging_down: bool = False
