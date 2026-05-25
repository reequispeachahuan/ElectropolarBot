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

SEACE_DEPARTMENT_CODES = {
    "AMAZONAS": "1",
    "ANCASH": "2",
    "APURIMAC": "3",
    "AREQUIPA": "4",
    "AYACUCHO": "5",
    "CAJAMARCA": "6",
    "CALLAO": "7",
    "CUSCO": "8",
    "HUANCAVELICA": "9",
    "HUANUCO": "10",
    "ICA": "11",
    "JUNIN": "12",
    "LA LIBERTAD": "13",
    "LAMBAYEQUE": "14",
    "LIMA": "15",
    "LORETO": "16",
    "MADRE DE DIOS": "17",
    "MOQUEGUA": "18",
    "PASCO": "19",
    "PIURA": "20",
    "PUNO": "21",
    "SAN MARTIN": "22",
    "TACNA": "23",
    "TUMBES": "24",
    "UCAYALI": "25",
}


def normalize_department(value: str) -> str:
    wanted = normalize_text(value)
    for department in SEACE_DEPARTMENTS:
        if normalize_text(department) == wanted:
            return department
    valid = ", ".join(SEACE_DEPARTMENTS)
    raise ValueError(f"Departamento SEACE no reconocido: {value}. Opciones: {valid}")


def normalize_departments(values: list[str]) -> list[str]:
    return [normalize_department(value) for value in values]


def department_code(value: str | None) -> str:
    if not value:
        return "0"
    department = normalize_department(value)
    try:
        return SEACE_DEPARTMENT_CODES[department]
    except KeyError as exc:
        raise ValueError(f"Departamento SEACE sin codigo API prod4: {department}") from exc
