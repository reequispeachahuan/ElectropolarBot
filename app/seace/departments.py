from __future__ import annotations

from app.utils.text_cleaner import normalize_text

SEACE_DEPARTMENTS = (
    "AMAZONAS",
    "ANCASH",
    "APURIMAC",
    "AREQUIPA",
    "AYACUCHO",
    "CAJAMARCA",
    "CALLAO",
    "CUSCO",
    "EXTERIOR",
    "HUANCAVELICA",
    "HUANUCO",
    "ICA",
    "JUNIN",
    "LA LIBERTAD",
    "LAMBAYEQUE",
    "LIMA",
    "LORETO",
    "MADRE DE DIOS",
    "MOQUEGUA",
    "MULTIDEPARTAMENTAL",
    "PASCO",
    "PIURA",
    "PUNO",
    "SAN MARTIN",
    "TACNA",
    "TUMBES",
    "UCAYALI",
)


def normalize_department(value: str) -> str:
    wanted = normalize_text(value)
    for department in SEACE_DEPARTMENTS:
        if normalize_text(department) == wanted:
            return department
    valid = ", ".join(SEACE_DEPARTMENTS)
    raise ValueError(f"Departamento SEACE no reconocido: {value}. Opciones: {valid}")


def normalize_departments(values: list[str]) -> list[str]:
    return [normalize_department(value) for value in values]
