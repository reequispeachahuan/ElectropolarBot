from datetime import date

from app.scoring.opportunity_score import score_opportunity


def test_scoring_recommends_urgent_for_good_solar_opportunity(monkeypatch):
    from app.scoring import opportunity_score

    monkeypatch.setattr(opportunity_score.settings, "attendable_regions", ["Lima"])
    result = score_opportunity(
        {
            "title": "Adquisición e instalación de 200 luminarias solares",
            "estimated_amount": 90000,
            "region": "Lima",
            "deadline": "2026-05-30",
            "documents_complete": True,
        },
        today=date(2026, 5, 18),
    )
    assert result.final_score == 100
    assert result.recommendation == "Postular urgente"


def test_scoring_penalizes_short_deadline_and_false_positive():
    result = score_opportunity(
        {
            "title": "Compra de batería para camioneta",
            "estimated_amount": 1000,
            "deadline": "2026-05-19",
            "false_positive": True,
        },
        today=date(2026, 5, 18),
    )
    assert result.final_score == 0
    assert result.recommendation == "Descartar"


def test_scoring_tolerates_seace_amount_placeholders():
    result = score_opportunity({"title": "Compra de panel solar", "estimated_amount": "---"})

    assert result.final_score >= 30
