from __future__ import annotations

import argparse
from datetime import date, timedelta

from app.classifier.opportunity_classifier import OpportunityClassifier
from app.config.settings import settings
from app.scoring.opportunity_score import score_opportunity
from app.seace.scraper import SearchQuery, SeaceScraper
from app.utils.logger import get_logger

logger = get_logger(__name__)


def run_once() -> list[dict[str, object]]:
    """Ejecuta una captura pública, clasifica y puntúa resultados.

    Persistencia y alertas se conectan en despliegue real con credenciales de BD
    y Telegram. Esta función devuelve oportunidades normalizadas para pruebas y
    orquestación.
    """
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
        processed.append(opportunity)
    logger.info("Oportunidades procesadas: %s", len(processed))
    return processed


def main() -> None:
    parser = argparse.ArgumentParser(description="SolarBot SEACE")
    parser.add_argument("--mode", choices=("once", "scheduler"), default="once")
    args = parser.parse_args()
    if args.mode == "scheduler":
        from app.jobs.scheduler import start_scheduler

        start_scheduler()
    else:
        run_once()


if __name__ == "__main__":
    main()
