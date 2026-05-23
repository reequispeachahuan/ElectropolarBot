from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.classifier.keyword_matcher import KeywordMatch
from app.classifier.opportunity_classifier import ClassificationResult
from app.database.models import Alert, Base, Opportunity, ScanRun
from app.database.repository import (
    RunStats,
    finish_scan_run,
    record_telegram_alert,
    save_processed_opportunity,
    start_scan_run,
    update_opportunity_status,
)
from app.scoring.opportunity_score import ScoreResult


def test_save_processed_opportunity_deduplicates_by_seace_code():
    session = _session()
    raw = {
        "source": "seace",
        "seace_code": "LP-001-2026",
        "title": "Compra de panel solar",
        "entity_name": "Municipalidad",
        "estimated_amount": "S/ 55,000.00",
        "publication_date": "22/05/2026",
    }
    classification = ClassificationResult(
        priority="alta",
        action="alertar_telegram_inmediato",
        score=70,
        matches=[KeywordMatch(keyword="panel solar", match_type="alta_prioridad", context="panel solar")],
    )
    score = ScoreResult(final_score=80, recommendation="Revisar hoy")

    first = save_processed_opportunity(session, raw, classification, score)
    second = save_processed_opportunity(session, raw, classification, score)

    assert first.created is True
    assert second.created is False
    assert session.scalar(select(Opportunity).where(Opportunity.seace_code == "LP-001-2026")).score == 80
    assert len(session.scalars(select(Opportunity)).all()) == 1


def test_record_telegram_alert_marks_existing_opportunity_as_alerted():
    session = _session()
    raw = {"source": "seace", "seace_code": "LP-002-2026", "title": "Luminarias solares"}
    classification = ClassificationResult(priority="alta", action="alertar_telegram_inmediato", score=70)
    score = ScoreResult(final_score=90, recommendation="Postular urgente")

    saved = save_processed_opportunity(session, raw, classification, score)
    record_telegram_alert(session, saved.opportunity.id, "mensaje", sent=True)
    again = save_processed_opportunity(session, raw, classification, score)

    assert again.already_alerted is True
    assert session.scalar(select(Alert.status)) == "enviado"


def test_scan_run_records_stats():
    session = _session()

    run = start_scan_run(session, ["solar"], ["TACNA"])
    finish_scan_run(session, run.id, "success", RunStats(processed_count=3, high_count=2, alerts_sent=1))

    saved = session.get(ScanRun, run.id)
    assert saved.status == "success"
    assert saved.processed_count == 3
    assert saved.high_count == 2
    assert saved.alerts_sent == 1


def test_update_opportunity_status():
    session = _session()
    raw = {"source": "seace", "seace_code": "LP-003-2026", "title": "Panel solar"}
    classification = ClassificationResult(priority="alta", action="alertar_telegram_inmediato", score=70)
    score = ScoreResult(final_score=90, recommendation="Postular urgente")
    saved = save_processed_opportunity(session, raw, classification, score)

    assert update_opportunity_status(session, saved.opportunity.id, "cotizar") is True
    assert session.get(Opportunity, saved.opportunity.id).status == "cotizar"


def _session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, future=True)()
