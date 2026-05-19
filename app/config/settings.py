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


def _csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///solarbot.db")
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")
    seace_headless: bool = os.getenv("SEACE_HEADLESS", "true").lower() == "true"
    attendable_regions: list[str] = field(default_factory=lambda: _csv(os.getenv("ATTENDABLE_REGIONS")))
    attractive_amount: float = float(os.getenv("ATTRACTIVE_AMOUNT", "50000"))
    data_dir: Path = Path(os.getenv("DATA_DIR", "data"))
    keywords_path: Path = Path(os.getenv("KEYWORDS_PATH", "app/config/solar_keywords.yml"))


settings = Settings()
