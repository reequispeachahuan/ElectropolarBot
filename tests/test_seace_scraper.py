from app.seace.scraper import SearchQuery, SeaceScraper


def test_normalize_procedimiento_row_maps_seace_columns():
    row = {
        "source": "procedimientos_seleccion",
        "nombre o sigla de la entidad": "Municipalidad Distrital",
        "fecha y hora de publicacion": "22/05/2026 10:00",
        "nomenclatura": "AS-SM-1-2026",
        "objeto de contratacion": "Bien",
        "descripcion de objeto": "Adquisicion de luminarias solares",
        "vr / ve / cuantia de la contratacion": "S/ 80,000.00",
    }

    opportunity = SeaceScraper._normalize(row, SearchQuery(keyword="solar"))

    assert opportunity["source"] == "procedimientos_seleccion"
    assert opportunity["seace_code"] == "AS-SM-1-2026"
    assert opportunity["title"] == "Adquisicion de luminarias solares"
    assert opportunity["entity_name"] == "Municipalidad Distrital"
    assert opportunity["estimated_amount"] == "S/ 80,000.00"


def test_normalize_uses_query_department_when_table_has_no_region():
    opportunity = SeaceScraper._normalize(
        {"source": "procedimientos_seleccion", "nomenclatura": "LP-001", "descripcion de objeto": "Panel solar"},
        SearchQuery(keyword="solar", department="TACNA"),
    )

    assert opportunity["region"] == "TACNA"


def test_has_identity_rejects_blank_rows():
    assert SeaceScraper._has_identity({"title": "", "description": None, "seace_code": None}) is False
    assert SeaceScraper._has_identity({"title": "Panel solar"}) is True


def test_page_count_from_primefaces_text():
    assert SeaceScraper._page_count_from_text("[ Mostrando de 1 a 15 del total 73 - Pagina: 1/5 ]") == 5
    assert SeaceScraper._page_count_from_text("1 de 1") == 1
    assert SeaceScraper._page_count_from_text("") == 1


def test_fallback_search_url_includes_seace_code():
    url = SeaceScraper._fallback_search_url("LP-001-2026")

    assert "buscadorPublico.xhtml" in url
    assert "LP-001-2026" in url


def test_normalize_openegocio_row_maps_api_fields():
    row = {
        "idProcedimiento": 1218601,
        "detEntidad": "Municipalidad Distrital",
        "detTipoProceso": "Licitacion Publica Abreviada",
        "nomenclatura": "LP-ABR-15-2026-MDCGAL-1",
        "detObjeto": "Bien",
        "detItem": "ADQUISICION DE PANELES SOLARES 615W",
        "detCubso": "PANEL SOLAR DE 75 W",
        "valorReferencialItem": "---",
        "fechaConvocatoria": "22/05/2026 16:33:00",
        "fechaFin": "01/06/2026 23:59:00",
        "nroItem": "1",
        "sintesisProceso": "Implementacion de paneles solares",
    }

    opportunity = SeaceScraper._normalize_openegocio_row(row, SearchQuery(keyword="solar", department="TACNA"))

    assert opportunity["source"] == "seace_oportunidades_negocio"
    assert opportunity["seace_code"] == "LP-ABR-15-2026-MDCGAL-1#1"
    assert opportunity["title"] == "ADQUISICION DE PANELES SOLARES 615W"
    assert opportunity["entity_name"] == "Municipalidad Distrital"
    assert opportunity["region"] == "TACNA"
    assert opportunity["estimated_amount"] == ""
    assert "1218601" in opportunity["seace_url"]
