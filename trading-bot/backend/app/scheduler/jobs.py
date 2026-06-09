from apscheduler.schedulers.background import BackgroundScheduler

from app.services import run_analysis, run_optimization, run_paper_trade, run_screening


def build_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="Asia/Tokyo")
    scheduler.add_job(run_screening, "cron", hour=8, minute=30, id="screening")
    scheduler.add_job(run_paper_trade, "cron", hour=9, minute=10, id="paper_trade")
    scheduler.add_job(run_analysis, "cron", hour=15, minute=30, id="daily_analysis")
    scheduler.add_job(run_optimization, "cron", hour=16, minute=0, id="optimization")
    return scheduler
