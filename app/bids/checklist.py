from __future__ import annotations

DEFAULT_CHECKLIST = (
    "Revisar bases",
    "Verificar RNP",
    "Verificar experiencia requerida",
    "Descargar anexos",
    "Preparar ficha técnica",
    "Preparar propuesta económica",
    "Preparar garantía, si aplica",
    "Preparar declaración jurada",
    "Preparar consultas u observaciones",
    "Validar fecha límite",
    "Confirmar responsable de presentación",
)


def render_checklist(items: tuple[str, ...] = DEFAULT_CHECKLIST) -> str:
    return "\n".join(f"- [ ] {item}" for item in items) + "\n"
