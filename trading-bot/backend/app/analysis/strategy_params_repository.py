from __future__ import annotations

import json
from datetime import date
from typing import Any

from app.db import execute, fetch_all, fetch_one
from app.models import STRATEGY_NAMES, StrategyParams


PARAM_FIELDS = (
    "take_profit_rate",
    "stop_loss_rate",
    "entry_start_time",
    "entry_end_time",
    "volume_spike_threshold",
    "breakout_threshold",
    "vwap_exit_enabled",
)


def latest_strategy_params(strategy_name: str) -> StrategyParams:
    row = fetch_one("SELECT * FROM strategy_params WHERE strategy_name = ? ORDER BY id DESC LIMIT 1", (strategy_name,))
    if not row:
        return StrategyParams(strategy_name=strategy_name)
    return _row_to_params(row)


def latest_params_for_all() -> dict[str, StrategyParams]:
    return {strategy_name: latest_strategy_params(strategy_name) for strategy_name in STRATEGY_NAMES}


def save_strategy_params(strategy_name: str, params: dict[str, Any], active_from: str) -> StrategyParams:
    normalized = normalize_strategy_params(strategy_name, params)
    execute(
        """
        INSERT INTO strategy_params(
          strategy_name, active_from, take_profit_rate, stop_loss_rate, entry_start_time,
          entry_end_time, volume_spike_threshold, breakout_threshold, vwap_exit_enabled
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            normalized.strategy_name,
            active_from,
            normalized.take_profit_rate,
            normalized.stop_loss_rate,
            normalized.entry_start_time,
            normalized.entry_end_time,
            normalized.volume_spike_threshold,
            normalized.breakout_threshold,
            1 if normalized.vwap_exit_enabled else 0,
        ),
    )
    return normalized


def adopt_experiment(strategy_name: str, proposed_params: dict[str, Any], experiment_date: date) -> StrategyParams:
    return save_strategy_params(strategy_name, proposed_params, active_from=f"adopted:{experiment_date.isoformat()}")


def adopted_experiments() -> list[dict[str, Any]]:
    return fetch_all("SELECT * FROM strategy_experiments WHERE adopted = 1 ORDER BY created_at DESC")


def normalize_strategy_params(strategy_name: str, raw_params: dict[str, Any]) -> StrategyParams:
    base = StrategyParams(strategy_name=strategy_name)
    return StrategyParams(
        strategy_name=strategy_name,
        take_profit_rate=_clamp_float(raw_params.get("take_profit_rate", base.take_profit_rate), 0.05, 0.25),
        stop_loss_rate=_clamp_float(raw_params.get("stop_loss_rate", base.stop_loss_rate), 0.03, 0.10),
        entry_start_time=_time_in_range(str(raw_params.get("entry_start_time", base.entry_start_time)), "09:05", "09:30", base.entry_start_time),
        entry_end_time=_time_in_range(str(raw_params.get("entry_end_time", base.entry_end_time)), "10:00", "11:00", base.entry_end_time),
        volume_spike_threshold=_clamp_float(raw_params.get("volume_spike_threshold", base.volume_spike_threshold), 2.0, 10.0),
        breakout_threshold=_clamp_float(raw_params.get("breakout_threshold", base.breakout_threshold), 0.0, 0.05),
        vwap_exit_enabled=bool(raw_params.get("vwap_exit_enabled", base.vwap_exit_enabled)),
    )


def params_to_json(params: StrategyParams) -> str:
    return json.dumps({field: getattr(params, field) for field in PARAM_FIELDS}, ensure_ascii=False)


def _row_to_params(row: dict[str, Any]) -> StrategyParams:
    return StrategyParams(
        strategy_name=str(row["strategy_name"]),
        take_profit_rate=float(row["take_profit_rate"]),
        stop_loss_rate=float(row["stop_loss_rate"]),
        entry_start_time=str(row["entry_start_time"]),
        entry_end_time=str(row["entry_end_time"]),
        volume_spike_threshold=float(row["volume_spike_threshold"]),
        breakout_threshold=float(row["breakout_threshold"]),
        vwap_exit_enabled=bool(row["vwap_exit_enabled"]),
    )


def _clamp_float(value: Any, lower: float, upper: float) -> float:
    number = float(value)
    return round(max(lower, min(upper, number)), 4)


def _time_in_range(value: str, lower: str, upper: str, fallback: str) -> str:
    if len(value) != 5 or value[2] != ":":
        return fallback
    return value if lower <= value <= upper else fallback
