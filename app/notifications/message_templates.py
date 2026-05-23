from __future__ import annotations

from html import escape
from typing import Any


def opportunity_alert(opportunity: dict[str, Any], matches: list[Any] | None = None) -> str:
    match_lines = "\n".join(
        f"- Coincide con {escape(str(m.keyword))} ({escape(str(m.match_type))})" for m in matches or []
    ) or "- Coincidencia solar detectada"
    return (
        "Nueva oportunidad solar en SEACE\n\n"
        f"Entidad: {_value(opportunity.get('entity_name'), 'No indicada')}\n"
        f"Codigo SEACE: {_value(opportunity.get('seace_code'), 'No indicado')}\n"
        f"Region: {_value(opportunity.get('region'), 'No indicada')}\n"
        f"Objeto: {_value(opportunity.get('object_type'), 'No indicado')}\n"
        f"Descripcion: {_value(opportunity.get('title') or opportunity.get('description'), 'Sin descripcion')}\n"
        f"Monto estimado: {_value(opportunity.get('estimated_amount'), 'No indicado')}\n"
        f"Prioridad: {escape(str(opportunity.get('priority') or '').upper())}\n"
        f"Puntaje: {escape(str(opportunity.get('score', 0)))}/100\n"
        f"Fecha limite: {_value(opportunity.get('deadline'), 'No indicada')}\n\n"
        "Motivo:\n"
        f"{match_lines}\n\n"
        "Acciones:\n"
        "- Revisar bases\n- Confirmar stock/proveedor\n- Preparar propuesta tecnica"
    )


def daily_summary(opportunities: list[dict[str, Any]]) -> str:
    lines = ["Resumen diario SolarBot SEACE", ""]
    for item in opportunities:
        lines.append(
            f"- [{escape(str(item.get('priority', 'baja')).upper())}] "
            f"{_value(item.get('title'), 'Sin titulo')} - {_value(item.get('entity_name'), 'Sin entidad')}"
        )
    return "\n".join(lines)


def _value(value: Any, fallback: str) -> str:
    return escape(str(value or fallback))
