from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.classifier.keyword_matcher import KeywordMatch, KeywordMatcher, PRIORITY_ORDER
from app.config.settings import settings

POINTS = {
    "alta_prioridad": 70,
    "media_prioridad": 45,
    "baja_prioridad": 20,
    "descartar": -100,
}
PRIORITY_BY_MATCH = {
    "alta_prioridad": "alta",
    "media_prioridad": "media",
    "baja_prioridad": "baja",
}


@dataclass(frozen=True)
class ClassificationResult:
    priority: str
    action: str
    score: int
    matches: list[KeywordMatch] = field(default_factory=list)
    discarded: bool = False


class OpportunityClassifier:
    def __init__(self, matcher: KeywordMatcher | None = None) -> None:
        self.matcher = matcher or KeywordMatcher(settings.keywords_path)

    def classify(self, opportunity: dict[str, Any]) -> ClassificationResult:
        matches = self.matcher.find_matches(
            opportunity.get("title"), opportunity.get("description"), opportunity.get("object_type")
        )
        discard_matches = [match for match in matches if match.match_type == "descartar"]
        if discard_matches:
            return ClassificationResult(
                priority="descartada",
                action="archivar_sin_alerta",
                score=0,
                matches=matches,
                discarded=True,
            )

        best_type = next((kind for kind in PRIORITY_ORDER if any(m.match_type == kind for m in matches)), None)
        if not best_type:
            return ClassificationResult(priority="baja", action="guardar_para_revision", score=0, matches=[])

        score = min(100, sum(POINTS.get(match.match_type, 0) for match in matches if match.match_type != "descartar"))
        priority = PRIORITY_BY_MATCH[best_type]
        action = {
            "alta": "alertar_telegram_inmediato",
            "media": "resumen_diario",
            "baja": "guardar_para_revision",
        }[priority]
        return ClassificationResult(priority=priority, action=action, score=score, matches=matches)
