from __future__ import annotations

from apscheduler.schedulers.blocking import BlockingScheduler

from app.config.settings import settings
from app.main import run_once, send_summary


def start_scheduler() -> None:
    scheduler = BlockingScheduler(timezone="America/Lima")
    scheduler.add_job(
        run_once,
        "cron",
        hour=settings.daily_scan_hour,
        minute=settings.daily_scan_minute,
        id="daily_seace_scan",
        replace_existing=True,
        jitter=settings.scan_jitter_minutes * 60,
    )
    scheduler.add_job(
        run_once,
        "interval",
        hours=settings.scan_interval_hours,
        id="periodic_seace_scan",
        replace_existing=True,
        jitter=settings.scan_jitter_minutes * 60,
    )
    scheduler.add_job(
        send_summary,
        "cron",
        hour=settings.daily_summary_hour,
        minute=settings.daily_summary_minute,
        id="daily_telegram_summary",
        replace_existing=True,
    )
    scheduler.start()
