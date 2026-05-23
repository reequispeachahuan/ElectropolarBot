import pytest

from app.seace.departments import normalize_department, normalize_departments


def test_normalize_department_accepts_seace_names_case_and_accents():
    assert normalize_department("tacna") == "TACNA"
    assert normalize_department("Áncash") == "ANCASH"


def test_normalize_departments_rejects_unknown_values():
    with pytest.raises(ValueError):
        normalize_departments(["Atlantis"])
