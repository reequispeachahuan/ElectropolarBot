from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.classifier.opportunity_classifier import ClassificationResult
from app.database.models import Alert, Evaluation, Match, Opportunity, ScanRun
from app.scoring.opportunity_score import ScoreResult
from app.utils.dates import parse_date


@dataclass(frozen=True)
class SaveResult:
    opportunity: Opportunity
    created: bool
    already_alerted: bool


@dataclass(frozen=True)
class RunStats:
    found_count: int = 0
    processed_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    discarded_count: int = 0
    alerts_sent: int = 0
    alerts_failed: int = 0


def save_processed_opportunity(
    session: Session,
    raw: dict[str, Any],
    classification: ClassificationResult,
    score: ScoreResult,
) -> SaveResult:
    if not _has_identity(raw):
        raise ValueError("La oportunidad no tiene titulo, descripcion ni codigo SEACE")

    db_opportunity = _find_existing(session, raw)
    created = db_opportunity is None
    if created:
        db_opportunity = Opportunity(
            source=str(raw.get("source") or "seace"),
            seace_code=_clean(raw.get("seace_code")),
            title=str(raw.get("title") or raw.get("description") or "Sin titulo"),
            status="descartada" if classification.discarded else "nueva",
        )
        session.add(db_opportunity)

    db_opportunity.title = str(raw.get("title") or raw.get("description") or "Sin titulo")
    db_opportunity.description = _clean(raw.get("description"))
    db_opportunity.entity_name = _clean(raw.get("entity_name"))
    db_opportunity.region = _clean(raw.get("region"))
    db_opportunity.object_type = _clean(raw.get("object_type"))
    db_opportunity.procedure_type = _clean(raw.get("procedure_type"))
    db_opportunity.estimated_amount = _decimal(raw.get("estimated_amount"))
    db_opportunity.publication_date = parse_date(raw.get("publication_date"))
    db_opportunity.deadline = parse_date(raw.get("deadline"))
    db_opportunity.priority = classification.priority
    db_opportunity.score = score.final_score
    db_opportunity.seace_url = _clean(raw.get("seace_url"))
    if classification.discarded:
        db_opportunity.status = "descartada"

    session.flush()
    already_alerted = has_sent_telegram_alert(session, db_opportunity.id)

    db_opportunity.matches.clear()
    db_opportunity.evaluations.clear()
    session.flush()

    for match in classification.matches:
        db_opportunity.matches.append(
            Match(keyword=match.keyword, match_type=match.match_type, context=match.context)
        )
    db_opportunity.evaluations.append(
        Evaluation(final_score=score.final_score, recommendation=score.recommendation)
    )

    session.commit()
    return SaveResult(opportunity=db_opportunity, created=created, already_alerted=already_alerted)


def has_sent_telegram_alert(session: Session, opportunity_id: str) -> bool:
    stmt = select(Alert.id).where(
        Alert.opportunity_id == opportunity_id,
        Alert.channel == "Telegram",
        Alert.status == "enviado",
    )
    return session.execute(stmt).first() is not None


def record_telegram_alert(
    session: Session,
    opportunity_id: str,
    message: str,
    sent: bool,
) -> None:
    session.add(
        Alert(
            opportunity_id=opportunity_id,
            channel="Telegram",
            sent_at=datetime.now(timezone.utc) if sent else None,
            message=message,
            status="enviado" if sent else "fallido",
        )
    )
    session.commit()


def start_scan_run(session: Session, keywords: list[str], departments: list[str]) -> ScanRun:
    run = ScanRun(
        keywords=", ".join(keywords),
        departments=", ".join(departments) if departments else "todos",
        status="running",
    )
    session.add(run)
    session.commit()
    return run


def finish_scan_run(
    session: Session,
    run_id: str,
    status: str,
    stats: RunStats | None = None,
    error_message: str | None = None,
) -> None:
    run = session.get(ScanRun, run_id)
    if run is None:
        return
    stats = stats or RunStats()
    run.finished_at = datetime.now(timezone.utc)
    run.status = status
    run.found_count = stats.found_count
    run.processed_count = stats.processed_count
    run.high_count = stats.high_count
    run.medium_count = stats.medium_count
    run.low_count = stats.low_count
    run.discarded_count = stats.discarded_count
    run.alerts_sent = stats.alerts_sent
    run.alerts_failed = stats.alerts_failed
    run.error_message = error_message
    session.commit()


def update_opportunity_status(session: Session, opportunity_id: str, status: str) -> bool:
    opportunity = session.get(Opportunity, opportunity_id)
    if opportunity is None:
        return False
    opportunity.status = status
    session.commit()
    return True


def _find_existing(session: Session, raw: dict[str, Any]) -> Opportunity | None:
    seace_code = _clean(raw.get("seace_code"))
    if seace_code:
        return session.execute(select(Opportunity).where(Opportunity.seace_code == seace_code)).scalar_one_or_none()

    title = str(raw.get("title") or raw.get("description") or "")
    if not title:
        return None
    stmt = select(Opportunity).where(
        Opportunity.source == str(raw.get("source") or "seace"),
        Opportunity.title == title,
        Opportunity.entity_name == _clean(raw.get("entity_name")),
    )
    return session.execute(stmt).scalar_one_or_none()


def _has_identity(raw: dict[str, Any]) -> bool:
    return any(_clean(raw.get(key)) for key in ("seace_code", "title", "description"))


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _decimal(value: Any) -> Decimal | None:
    if value in (None, ""):
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int | float):
        return Decimal(str(value))

    text = re.sub(r"[^\d,.\-]", "", str(value))
    if not text:
        return None
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(",", ".")
    try:
        return Decimal(text)
    except InvalidOperation:
        return None
