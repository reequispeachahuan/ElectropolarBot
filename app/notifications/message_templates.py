from __future__ import annotations

from typing import Any


def opportunity_alert(opportunity: dict[str, Any], matches: list[Any] | None = None) -> str:
    match_lines = "\n".join(f'- Coincide con “{m.keyword}” ({m.match_type})' for m in matches or []) or "- Coincidencia solar detectada"
    return (
        "🚨 Nueva oportunidad solar en SEACE\n\n"
        f"Entidad: {opportunity.get('entity_name') or 'No indicada'}\n"
        f"Objeto: {opportunity.get('object_type') or 'No indicado'}\n"
        f"Descripción: {opportunity.get('title') or opportunity.get('description') or 'Sin descripción'}\n"
        f"Monto estimado: {opportunity.get('estimated_amount') or 'No indicado'}\n"
        f"Prioridad: {str(opportunity.get('priority') or '').upper()}\n"
        f"Puntaje: {opportunity.get('score', 0)}/100\n"
        f"Fecha límite: {opportunity.get('deadline') or 'No indicada'}\n\n"
        "Motivo:\n"
        f"{match_lines}\n\n"
        "Acciones:\n"
        "✅ Revisar bases\n✅ Confirmar stock/proveedor\n✅ Preparar propuesta técnica"
    )


def daily_summary(opportunities: list[dict[str, Any]]) -> str:
    lines = ["📋 Resumen diario SolarBot SEACE", ""]
    for item in opportunities:
        lines.append(f"• [{str(item.get('priority', 'baja')).upper()}] {item.get('title')} — {item.get('entity_name')}")
    return "\n".join(lines)
