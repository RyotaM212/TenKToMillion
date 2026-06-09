from apscheduler.schedulers.background import BackgroundScheduler

from app.llm.analyst_service import AnalystService
from app.services import run_analysis, run_optimization, run_paper_trade, run_screening


def build_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="Asia/Tokyo")
    scheduler.add_job(run_screening, "cron", hour=8, minute=30, id="screening")
    scheduler.add_job(run_paper_trade, "cron", hour=9, minute=10, id="paper_trade")
    scheduler.add_job(run_analysis, "cron", hour=15, minute=30, id="daily_analysis")
    scheduler.add_job(_run_llm_daily_analysis, "cron", hour=15, minute=45, id="llm_daily_analysis")
    scheduler.add_job(_backtest_llm_proposals, "cron", hour=16, minute=0, id="llm_backtest_proposals")
    scheduler.add_job(run_optimization, "cron", hour=16, minute=15, id="optimization")
    return scheduler


def _run_llm_daily_analysis() -> None:
    from datetime import date

    AnalystService().run_daily_analysis(date.today())


def _backtest_llm_proposals() -> None:
    AnalystService().backtest_latest_proposals()
