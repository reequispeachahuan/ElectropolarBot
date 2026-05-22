from __future__ import annotations

from typing import Any


def generate_executive_summary(opportunity: dict[str, Any], risks: list[str] | None = None) -> str:
    return "\n".join(
        [
            f"# {opportunity.get('title', 'Oportunidad SEACE')}",
            "",
            f"- Entidad: {opportunity.get('entity_name', 'No indicada')}",
            f"- Objeto: {opportunity.get('object_type', 'No indicado')}",
            f"- Monto: {opportunity.get('estimated_amount', 'No indicado')}",
            f"- Fecha límite: {opportunity.get('deadline', 'No indicada')}",
            f"- Recomendación: {opportunity.get('recommendation', 'Pendiente')}",
            "",
            "## Riesgos",
            *(f"- {risk}" for risk in (risks or ["Pendiente de revisión técnica y legal"])),
        ]
    )
