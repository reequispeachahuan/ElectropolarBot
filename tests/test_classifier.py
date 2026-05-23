from app.classifier.opportunity_classifier import OpportunityClassifier


def test_high_priority_solar_luminaires():
    result = OpportunityClassifier().classify(
        {"title": "Adquisicion de 120 luminarias solares para alumbrado publico"}
    )
    assert result.priority == "alta"
    assert result.action == "alertar_telegram_inmediato"
    assert any(match.keyword == "luminarias solares" for match in result.matches)


def test_medium_priority_public_lighting_maintenance():
    result = OpportunityClassifier().classify({"title": "Servicio de mantenimiento de alumbrado publico"})
    assert result.priority == "media"
    assert result.action == "resumen_diario"


def test_false_positive_is_discarded():
    result = OpportunityClassifier().classify({"title": "Compra de bateria para camioneta municipal"})
    assert result.priority == "descartada"
    assert result.discarded is True


def test_solar_opportunity_with_secondary_generator_is_not_discarded():
    result = OpportunityClassifier().classify(
        {"title": "Servicio de mantenimiento de paneles fotovoltaico, congeladora solar y grupo electrogeno"}
    )
    assert result.priority == "alta"
    assert result.discarded is False


def test_sunscreen_false_positive_is_discarded():
    result = OpportunityClassifier().classify({"title": "Adquisicion de protector solar para personal operativo"})
    assert result.priority == "descartada"
    assert result.discarded is True


def test_solar_protection_false_positive_is_discarded():
    result = OpportunityClassifier().classify({"title": "Adquisicion de bloqueadores solares para personal"})
    assert result.priority == "descartada"
    assert result.discarded is True

    result = OpportunityClassifier().classify({"title": "Servicio de proteccion solar para patio multiusos"})
    assert result.priority == "descartada"
    assert result.discarded is True
