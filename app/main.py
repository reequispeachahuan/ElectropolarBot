from __future__ import annotations

import argparse
import asyncio
from datetime import date, timedelta
from collections import Counter
import yaml
from sqlalchemy import select

from app.classifier.opportunity_classifier import OpportunityClassifier
from app.config.settings import settings
from app.database.models import Opportunity
from app.database.repository import (
    RunStats,
    finish_scan_run,
    record_telegram_alert,
    save_processed_opportunity,
    start_scan_run,
)
from app.database.session import SessionLocal, init_db
from app.notifications.message_templates import daily_summary, opportunity_alert
from app.notifications.telegram_bot import TelegramNotifier
from app.reports.opportunities import export_opportunities_csv, print_opportunities
from app.scoring.opportunity_score import ScoreResult, score_opportunity
from app.seace.departments import SEACE_DEPARTMENTS, normalize_departments
from app.seace.scraper import SearchQuery, SeaceScraper
from app.utils.logger import get_logger

logger = get_logger(__name__)


def run_once(search_keywords: list[str] | None = None, departments: list[str] | None = None) -> list[dict[str, object]]:
    """Run one public scan, classify, persist, and alert results."""
    init_db()
    classifier = OpportunityClassifier()
    scraper = SeaceScraper()
    date_to = date.today()
    queries = _build_queries(search_keywords, departments, date_to)
    processed: list[dict[str, object]] = []
    run_id: str | None = None
    stats = RunStats()
    with SessionLocal() as session:
        run = start_scan_run(
            session,
            keywords=sorted({query.keyword for query in queries}),
            departments=sorted({query.department for query in queries if query.department}),
        )
        run_id = run.id

    try:
        opportunities = _dedupe_opportunities(item for query in queries for item in scraper.search(query))
        alert_counts = Counter()
        priority_counts = Counter()

        with SessionLocal() as session:
            for opportunity in opportunities:
                classification = classifier.classify(opportunity)
                opportunity["priority"] = classification.priority
                opportunity["classification_score"] = classification.score
                if classification.discarded:
                    score = ScoreResult(final_score=0, recommendation="Descartar", reasons=["Descartado por regla"])
                else:
                    score = score_opportunity(opportunity)
                opportunity["score"] = score.final_score
                opportunity["recommendation"] = score.recommendation

                saved = save_processed_opportunity(session, opportunity, classification, score)
                opportunity["db_id"] = saved.opportunity.id
                opportunity["created"] = saved.created
                priority_counts[classification.priority] += 1

                if _should_send_telegram_alert(classification.priority, saved.already_alerted):
                    message = opportunity_alert(opportunity, classification.matches)
                    try:
                        asyncio.run(TelegramNotifier().send_message(message, opportunity.get("seace_url")))
                        record_telegram_alert(session, saved.opportunity.id, message, sent=True)
                        opportunity["telegram_alert"] = "sent"
                        alert_counts["sent"] += 1
                    except Exception:
                        record_telegram_alert(session, saved.opportunity.id, message, sent=False)
                        opportunity["telegram_alert"] = "failed"
                        alert_counts["failed"] += 1
                        logger.exception("No se pudo enviar alerta Telegram para %s", saved.opportunity.id)

                processed.append(opportunity)

        stats = RunStats(
            found_count=len(opportunities),
            processed_count=len(processed),
            high_count=priority_counts["alta"],
            medium_count=priority_counts["media"],
            low_count=priority_counts["baja"],
            discarded_count=priority_counts["descartada"],
            alerts_sent=alert_counts["sent"],
            alerts_failed=alert_counts["failed"],
        )
        with SessionLocal() as session:
            finish_scan_run(session, run_id, "success", stats)

        logger.info("Oportunidades procesadas: %s", len(processed))
        csv_path = export_opportunities_csv()
        logger.info("Resultados exportados a %s", csv_path)
        if not processed:
            _send_admin_warning("SolarBot SEACE no encontro oportunidades en la ultima corrida.")
        return processed
    except Exception as exc:
        with SessionLocal() as session:
            finish_scan_run(session, run_id, "failed", stats, error_message=str(exc))
        _send_admin_warning(f"SolarBot SEACE fallo durante la corrida: {exc}")
        raise


def _build_queries(
    search_keywords: list[str] | None,
    departments: list[str] | None,
    date_to: date,
) -> list[SearchQuery]:
    keywords = [keyword.strip() for keyword in (search_keywords or settings.search_keywords) if keyword.strip()]
    selected_departments = normalize_departments(departments if departments is not None else settings.seace_departments)
    if not keywords:
        keywords = ["solar"]
    departments_or_all: list[str | None] = selected_departments or [None]

    queries = [
        SearchQuery(
            keyword=keyword,
            department=department,
            date_from=date_to - timedelta(days=1),
            date_to=date_to,
        )
        for keyword in keywords
        for department in departments_or_all
    ]
    logger.info(
        "Consultas preparadas: keywords=%s departamentos=%s",
        ", ".join(keywords),
        ", ".join(selected_departments) if selected_departments else "todos",
    )
    return queries


def _dedupe_opportunities(opportunities) -> list[dict[str, object]]:
    seen: set[tuple[object, object, object]] = set()
    deduped: list[dict[str, object]] = []
    for opportunity in opportunities:
        key = (
            opportunity.get("source"),
            opportunity.get("seace_code"),
            opportunity.get("title"),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(opportunity)
    return deduped


def _csv_arg(value: str | None) -> list[str] | None:
    if value is None:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def _print_regions() -> None:
    for department in SEACE_DEPARTMENTS:
        print(department)


def _print_keywords() -> None:
    print("SEACE_SEARCH_KEYWORDS:")
    for keyword in settings.search_keywords:
        print(f"- {keyword}")
    print(f"\nClasificacion ({settings.keywords_path}):")
    with settings.keywords_path.open(encoding="utf-8") as handle:
        categories = yaml.safe_load(handle) or {}
    for category, words in categories.items():
        print(f"{category}:")
        for word in words or []:
            print(f"- {word}")


async def _test_telegram() -> None:
    notifier = TelegramNotifier()
    bot_name = await notifier.test_connection()
    logger.info("Bot Telegram conectado: %s", bot_name)
    if settings.telegram_chat_id:
        await notifier.send_message("SolarBot SEACE: prueba de Telegram OK")
        logger.info("Mensaje de prueba enviado")
    else:
        logger.warning("Falta TELEGRAM_CHAT_ID. Usa --mode telegram-chat-id despues de escribirle al bot.")


async def _print_telegram_chat_ids() -> None:
    chats = await TelegramNotifier().recent_chats()
    if not chats:
        print("No hay chats recientes. Escribele un mensaje al bot en Telegram y vuelve a ejecutar este comando.")
        return
    for chat in chats:
        username = f" @{chat.username}" if chat.username else ""
        print(f"{chat.chat_id} | {chat.chat_type} | {chat.title}{username}")


def send_summary() -> None:
    if not _telegram_ready() or not settings.telegram_summary_enabled:
        logger.info("Resumen Telegram no enviado: Telegram deshabilitado o sin credenciales")
        return
    priorities = set(settings.telegram_summary_priorities)
    with SessionLocal() as session:
        opportunities = list(
            session.scalars(
                select(Opportunity)
                .where(Opportunity.priority.in_(priorities))
                .order_by(Opportunity.score.desc(), Opportunity.created_at.desc())
                .limit(settings.telegram_summary_limit)
            ).all()
        )
    if not opportunities:
        logger.info("No hay oportunidades para resumen Telegram")
        return
    payload = [
        {
            "priority": item.priority,
            "title": item.title,
            "entity_name": item.entity_name,
            "score": item.score,
        }
        for item in opportunities
    ]
    asyncio.run(TelegramNotifier().send_message(daily_summary(payload)))
    logger.info("Resumen Telegram enviado con %s oportunidades", len(opportunities))


def _send_admin_warning(message: str) -> None:
    if not settings.telegram_error_alerts or not _telegram_ready():
        return
    try:
        asyncio.run(TelegramNotifier().send_message(message))
    except Exception:
        logger.exception("No se pudo enviar alerta administrativa por Telegram")


def _telegram_ready() -> bool:
    return settings.telegram_enabled and bool(settings.telegram_bot_token and settings.telegram_chat_id)


def _should_send_telegram_alert(priority: str, already_alerted: bool) -> bool:
    if already_alerted:
        return False
    if not _telegram_ready():
        return False
    if priority not in settings.telegram_alert_priorities:
        return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="SolarBot SEACE")
    parser.add_argument(
        "--mode",
        choices=(
            "once",
            "scheduler",
            "init-db",
            "test-telegram",
            "telegram-chat-id",
            "send-summary",
            "list",
            "export-csv",
            "list-regions",
            "list-keywords",
        ),
        default="once",
    )
    parser.add_argument("--limit", type=int, default=20, help="Cantidad de resultados para --mode list")
    parser.add_argument("--priority", choices=("alta", "media", "baja", "descartada"), help="Filtro para --mode list")
    parser.add_argument("--keywords", help="Keywords de busqueda SEACE separados por coma")
    parser.add_argument("--departments", help="Departamentos SEACE separados por coma. Vacio usa todos")
    args = parser.parse_args()
    if args.mode == "scheduler":
        from app.jobs.scheduler import start_scheduler

        start_scheduler()
    elif args.mode == "init-db":
        init_db()
        logger.info("Base de datos inicializada")
    elif args.mode == "test-telegram":
        asyncio.run(_test_telegram())
    elif args.mode == "telegram-chat-id":
        asyncio.run(_print_telegram_chat_ids())
    elif args.mode == "send-summary":
        send_summary()
    elif args.mode == "list":
        print_opportunities(limit=args.limit, priority=args.priority)
    elif args.mode == "export-csv":
        csv_path = export_opportunities_csv()
        logger.info("Resultados exportados a %s", csv_path)
    elif args.mode == "list-regions":
        _print_regions()
    elif args.mode == "list-keywords":
        _print_keywords()
    else:
        run_once(search_keywords=_csv_arg(args.keywords), departments=_csv_arg(args.departments))


if __name__ == "__main__":
    main()
