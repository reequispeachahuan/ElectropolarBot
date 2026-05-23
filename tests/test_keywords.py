from app.classifier.keyword_matcher import KeywordMatcher


def test_keyword_matcher_ignores_accents_and_case():
    matcher = KeywordMatcher("app/config/solar_keywords.yml")
    matches = matcher.find_matches("Servicio de INSTALACIÓN ELÉCTRICA para sistema de energía")
    keywords = {match.keyword for match in matches}
    assert "instalacion electrica" in keywords
    assert "sistema de energia" in keywords
