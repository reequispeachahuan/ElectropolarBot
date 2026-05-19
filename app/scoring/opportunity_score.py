from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from app.config.settings import settings
from app.utils.dates import days_until, parse_date
from app.utils.text_cleaner import normalize_text


@dataclass(frozen=True)
class ScoreResult:
    final_score: int
    recommendation: str
    reasons: list[str] = field(default_factory=list)


def score_opportunity(opportunity: dict[str, Any], today: date | None = None) -> ScoreResult:
    score = 0
    reasons: list[str] = []
    text = normalize_text(" ".join(str(opportunity.get(k) or "") for k in ("title", "description")))

    if any(word in text for word in ("solar", "fotovoltaico", "luminaria solar", "luminarias solares")):
        score += 30
        reasons.append("Rubro solar directo (+30)")

    amount = float(opportunity.get("estimated_amount") or 0)
    if amount >= settings.attractive_amount:
        score += 20
        reasons.append("Monto atractivo (+20)")

    region = normalize_text(opportunity.get("region"))
    if region and any(normalize_text(item) == region for item in settings.attendable_regions):
        score += 15
        reasons.append("Región atendible (+15)")

    deadline = parse_date(opportunity.get("deadline"))
    remaining = days_until(deadline, today)
    if remaining is not None:
        if remaining >= 7:
            score += 15
            reasons.append("Plazo suficiente (+15)")
        elif remaining < 3:
            score -= 20
            reasons.append("Plazo muy corto (-20)")

    if opportunity.get("technical_fit", True):
        score += 10
        reasons.append("Requisitos técnicos compatibles (+10)")
    if opportunity.get("experience_fit", True):
        score += 10
        reasons.append("Experiencia compatible (+10)")
    if opportunity.get("documents_complete"):
        score += 5
        reasons.append("Documentos completos (+5)")
    if opportunity.get("complex_work_required"):
        score -= 25
        reasons.append("Requiere obra compleja no cubierta (-25)")
    if opportunity.get("false_positive"):
        score -= 50
        reasons.append("Falso positivo (-50)")

    final = max(0, min(100, score))
    return ScoreResult(final_score=final, recommendation=_recommendation(final), reasons=reasons)


def _recommendation(score: int) -> str:
    if score >= 85:
        return "Postular urgente"
    if score >= 70:
        return "Revisar hoy"
    if score >= 50:
        return "Evaluar con técnico"
    if score >= 30:
        return "Baja prioridad"
    return "Descartar"
