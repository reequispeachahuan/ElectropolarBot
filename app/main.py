from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

from app.classifier.opportunity_classifier import OpportunityClassifier
from app.notifications.message_templates import daily_summary, opportunity_alert
from app.notifications.telegram_bot import TelegramNotifier
from app.scoring.opportunity_score import score_opportunity
from app.seace.scraper import SearchQuery, SeaceScraper
from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _persist_processed(processed: list[dict[str, object]]) -> Path | None:
    if not processed:
        return None
    output_dir = settings.data_dir / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_file = output_dir / f"opportunities_{timestamp}.csv"
    latest_file = output_dir / "latest_opportunities.csv"

    serializable: list[dict[str, object]] = []
    for row in processed:
        item = dict(row)
        item["matches"] = ", ".join(getattr(m, "keyword", str(m)) for m in item.get("matches", []))
        serializable.append(item)

    df = pd.DataFrame(serializable)
    df.to_csv(run_file, index=False)
    df.to_csv(latest_file, index=False)
    return run_file


def run_once(send_telegram: bool = False) -> list[dict[str, object]]:
    """Ejecuta una captura pública, clasifica y puntúa resultados."""
    classifier = OpportunityClassifier()
    scraper = SeaceScraper()
    date_to = date.today()
    query = SearchQuery(keyword="solar", date_from=date_to - timedelta(days=1), date_to=date_to)
    opportunities = scraper.search(query)

    processed: list[dict[str, object]] = []
    for opportunity in opportunities:
        classification = classifier.classify(opportunity)
        opportunity["priority"] = classification.priority
        opportunity["classification_score"] = classification.score
        score = score_opportunity(opportunity)
        opportunity["score"] = score.final_score
        opportunity["recommendation"] = score.recommendation
        opportunity["matches"] = classification.matches
        processed.append(opportunity)

    if send_telegram and processed:
        notifier = TelegramNotifier()
        high_priority = [item for item in processed if item.get("priority") == "alta"]
        for item in high_priority:
            notifier.send_message_sync(opportunity_alert(item, item.get("matches")), seace_url=item.get("seace_url"))
        notifier.send_message_sync(daily_summary(processed))

    persisted_file = _persist_processed(processed)
    logger.info("Oportunidades procesadas: %s", len(processed))
    if persisted_file is not None:
        logger.info("Resultados guardados en: %s", persisted_file)
    return processed


def send_telegram_test() -> None:
    notifier = TelegramNotifier()
    notifier.send_message_sync("✅ SolarBot SEACE conectado. Esta es una alerta de prueba.")


def main() -> None:
    parser = argparse.ArgumentParser(description="SolarBot SEACE")
    parser.add_argument("--mode", choices=("once", "scheduler", "telegram-test"), default="once")
    parser.add_argument("--send-telegram", action="store_true", help="Envía alertas Telegram en modo once")
    args = parser.parse_args()

    if args.mode == "scheduler":
        from app.jobs.scheduler import start_scheduler

        start_scheduler()
    elif args.mode == "telegram-test":
        send_telegram_test()
    else:
        run_once(send_telegram=args.send_telegram)


if __name__ == "__main__":
    main()
