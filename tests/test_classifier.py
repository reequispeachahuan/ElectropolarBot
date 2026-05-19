from app.classifier.opportunity_classifier import OpportunityClassifier


def test_high_priority_solar_luminaires():
    result = OpportunityClassifier().classify(
        {"title": "Adquisición de 120 luminarias solares para alumbrado público"}
    )
    assert result.priority == "alta"
    assert result.action == "alertar_telegram_inmediato"
    assert any(match.keyword == "luminarias solares" for match in result.matches)


def test_medium_priority_public_lighting_maintenance():
    result = OpportunityClassifier().classify({"title": "Servicio de mantenimiento de alumbrado público"})
    assert result.priority == "media"
    assert result.action == "resumen_diario"


def test_false_positive_is_discarded():
    result = OpportunityClassifier().classify({"title": "Compra de batería para camioneta municipal"})
    assert result.priority == "descartada"
    assert result.discarded is True
