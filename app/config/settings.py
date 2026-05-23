from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv() -> None:
        return None

load_dotenv()


def _env(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value is not None:
        return value
    file_path = os.getenv(f"{name}_FILE")
    if file_path:
        try:
            return Path(file_path).read_text(encoding="utf-8").strip()
        except OSError:
            return default
    return default


def _csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass
class Settings:
    database_url: str = _env("DATABASE_URL", "sqlite:///solarbot.db")
    telegram_bot_token: str = _env("TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = _env("TELEGRAM_CHAT_ID")
    seace_headless: bool = os.getenv("SEACE_HEADLESS", "true").lower() == "true"
    attendable_regions: list[str] = field(default_factory=lambda: _csv(os.getenv("ATTENDABLE_REGIONS")))
    attractive_amount: float = float(os.getenv("ATTRACTIVE_AMOUNT", "50000"))
    data_dir: Path = Path(os.getenv("DATA_DIR", "data"))
    keywords_path: Path = Path(os.getenv("KEYWORDS_PATH", "app/config/solar_keywords.yml"))
    search_keywords: list[str] = field(default_factory=lambda: _csv(os.getenv("SEACE_SEARCH_KEYWORDS", "solar")))
    seace_departments: list[str] = field(default_factory=lambda: _csv(os.getenv("SEACE_DEPARTMENTS")))
    scan_interval_hours: int = int(os.getenv("SCAN_INTERVAL_HOURS", "3"))
    daily_scan_hour: int = int(os.getenv("DAILY_SCAN_HOUR", "6"))
    daily_scan_minute: int = int(os.getenv("DAILY_SCAN_MINUTE", "0"))
    daily_summary_hour: int = int(os.getenv("DAILY_SUMMARY_HOUR", "18"))
    daily_summary_minute: int = int(os.getenv("DAILY_SUMMARY_MINUTE", "0"))
    seace_max_pages: int = int(os.getenv("SEACE_MAX_PAGES", "0"))
    seace_capture_detail_urls: bool = _bool(os.getenv("SEACE_CAPTURE_DETAIL_URLS"), False)
    results_csv_path: Path = Path(os.getenv("RESULTS_CSV_PATH", "data/processed/opportunities.csv"))
    telegram_alert_priorities: list[str] = field(
        default_factory=lambda: _csv(os.getenv("TELEGRAM_ALERT_PRIORITIES", "alta"))
    )
    telegram_summary_enabled: bool = _bool(os.getenv("TELEGRAM_SUMMARY_ENABLED"), True)
    telegram_summary_priorities: list[str] = field(
        default_factory=lambda: _csv(os.getenv("TELEGRAM_SUMMARY_PRIORITIES", "media,baja"))
    )
    telegram_summary_limit: int = int(os.getenv("TELEGRAM_SUMMARY_LIMIT", "15"))
    telegram_error_alerts: bool = _bool(os.getenv("TELEGRAM_ERROR_ALERTS"), True)
    telegram_enabled: bool = _bool(os.getenv("TELEGRAM_ENABLED"), True)


settings = Settings()
