from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.analysis.optimizer import latest_experiments
from app.config import get_settings
from app.analysis.strategy_evaluator import StrategyEvaluator
from app.db import fetch_all, init_db
from app.scheduler.jobs import build_scheduler
from app.services import dashboard, default_strategy_params, run_analysis, run_optimization, run_paper_trade, run_screening, set_app_state


app = FastAPI(title="TenKToMillion Paper Trading API")
scheduler = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(get_settings().cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class StateRequest(BaseModel):
    value: str


@app.on_event("startup")
def startup() -> None:
    global scheduler
    init_db()
    if get_settings().scheduler_enabled:
        scheduler = build_scheduler()
        scheduler.start()


@app.on_event("shutdown")
def shutdown() -> None:
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)


@app.get("/api/health")
def get_health():
    return {"ok": True, "scheduler_enabled": get_settings().scheduler_enabled}


@app.get("/api/dashboard")
def get_dashboard():
    return dashboard()


@app.get("/api/candidates/today")
def get_candidates_today():
    return fetch_all("SELECT * FROM candidates ORDER BY score DESC LIMIT 20")


@app.get("/api/market-snapshots")
def get_market_snapshots():
    return fetch_all("SELECT * FROM market_snapshots ORDER BY created_at DESC LIMIT 200")


@app.get("/api/trades")
def get_trades():
    return fetch_all("SELECT * FROM paper_trades ORDER BY created_at DESC LIMIT 200")


@app.get("/api/positions")
def get_positions():
    return fetch_all("SELECT * FROM paper_positions ORDER BY updated_at DESC")


@app.get("/api/reports/daily")
def get_daily_reports():
    return fetch_all("SELECT * FROM daily_reports ORDER BY created_at DESC LIMIT 200")


@app.get("/api/strategy/params")
def get_strategy_params():
    return default_strategy_params()


@app.get("/api/strategy/comparison")
def get_strategy_comparison():
    evaluator = StrategyEvaluator()
    return {"strategies": evaluator.comparison(), "modes": evaluator.mode_comparison()}


@app.get("/api/experiments")
def get_experiments():
    return latest_experiments()


@app.post("/api/bot/run-screening")
def post_run_screening():
    return run_screening()


@app.post("/api/bot/run-paper-trade")
def post_run_paper_trade():
    return run_paper_trade()


@app.post("/api/bot/run-analysis")
def post_run_analysis():
    return run_analysis()


@app.post("/api/bot/run-optimization")
def post_run_optimization():
    return run_optimization()


@app.post("/api/bot/set-mode")
def post_set_mode(request: StateRequest):
    return _set_state_or_400("mode", request.value)


@app.post("/api/bot/set-data-source")
def post_set_data_source(request: StateRequest):
    return _set_state_or_400("data_source", request.value)


@app.post("/api/bot/set-strategy")
def post_set_strategy(request: StateRequest):
    return _set_state_or_400("active_strategy", request.value)


def _set_state_or_400(key: str, value: str):
    try:
        return set_app_state(key, value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
