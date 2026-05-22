from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

from app.classifier.opportunity_classifier import OpportunityClassifier
from app.config.settings import settings
from app.notifications.message_templates import daily_summary, opportunity_alert
from app.notifications.telegram_bot import TelegramNotifier
from app.scoring.opportunity_score import score_opportunity
from app.seace.scraper import SearchQuery, SeaceScraper
from app.utils.logger import get_logger
from app.utils.text_cleaner import normalize_text

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


def _fetch_opportunities(scraper: SeaceScraper, keywords: list[str], date_from: date, date_to: date) -> list[dict[str, object]]:
    all_items: list[dict[str, object]] = []
    for keyword in keywords:
        query = SearchQuery(keyword=keyword, date_from=date_from, date_to=date_to)
        all_items.extend(scraper.search(query))

    deduped: dict[str, dict[str, object]] = {}
    for item in all_items:
        key = str(item.get("seace_code") or "") or normalize_text(str(item.get("title") or ""))
        deduped[key] = item
    return list(deduped.values())


def run_once(
    send_telegram: bool = False,
    keywords: list[str] | None = None,
    regions: list[str] | None = None,
) -> list[dict[str, object]]:
    """Ejecuta una captura pública, clasifica y puntúa resultados."""
    classifier = OpportunityClassifier()
    scraper = SeaceScraper()
    date_to = date.today()
    date_from = date_to - timedelta(days=1)

    active_keywords = [item.strip() for item in (keywords or ["solar"]) if item.strip()]
    active_regions = [normalize_text(item) for item in (regions or []) if item.strip()]

    opportunities = _fetch_opportunities(scraper, active_keywords, date_from=date_from, date_to=date_to)
    if active_regions:
        opportunities = [
            item for item in opportunities if normalize_text(str(item.get("region") or "")) in active_regions
        ]

    processed: list[dict[str, object]] = []
    for opportunity in opportunities:
        classification = classifier.classify(opportunity)
        opportunity["priority"] = classification.priority
        opportunity["classification_score"] = classification.score
        score = score_opportunity(opportunity)
        opportunity["score"] = score.final_score
        opportunity["recommendation"] = score.recommendation
        opportunity["matches"] = classification.matches
        opportunity["search_keywords"] = ", ".join(active_keywords)
        opportunity["search_regions"] = ", ".join(regions or [])
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
    parser.add_argument("--keywords", default="solar", help="Palabras clave separadas por coma")
    parser.add_argument("--regions", default="", help="Regiones separadas por coma")
    args = parser.parse_args()

    if args.mode == "scheduler":
        from app.jobs.scheduler import start_scheduler

        start_scheduler()
    elif args.mode == "telegram-test":
        send_telegram_test()
    else:
        keywords = [item.strip() for item in args.keywords.split(",") if item.strip()]
        regions = [item.strip() for item in args.regions.split(",") if item.strip()]
        run_once(send_telegram=args.send_telegram, keywords=keywords, regions=regions)


if __name__ == "__main__":
    main()
