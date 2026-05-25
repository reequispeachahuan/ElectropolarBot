import pytest

from app.seace.departments import department_code, normalize_department, normalize_departments


def test_normalize_department_accepts_seace_names_case_and_accents():
    assert normalize_department("tacna") == "TACNA"
    assert normalize_department("Áncash") == "ANCASH"


def test_normalize_departments_rejects_unknown_values():
    with pytest.raises(ValueError):
        normalize_departments(["Atlantis"])


def test_department_code_for_openegocio_api():
    assert department_code("tacna") == "23"
    assert department_code(None) == "0"
