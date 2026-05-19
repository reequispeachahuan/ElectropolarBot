from __future__ import annotations

from apscheduler.schedulers.blocking import BlockingScheduler

from app.main import run_once


def start_scheduler() -> None:
    scheduler = BlockingScheduler(timezone="America/Lima")
    scheduler.add_job(run_once, "cron", hour=6, minute=0, id="daily_seace_scan")
    scheduler.add_job(run_once, "interval", hours=3, id="periodic_seace_scan")
    scheduler.start()
