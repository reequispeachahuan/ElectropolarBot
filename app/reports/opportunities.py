from __future__ import annotations

import csv
from pathlib import Path

from sqlalchemy import case, select

from app.config.settings import settings
from app.database.models import Opportunity
from app.database.session import SessionLocal, init_db

EXPORT_COLUMNS = [
    "priority",
    "score",
    "status",
    "publication_date",
    "deadline",
    "entity_name",
    "seace_code",
    "object_type",
    "procedure_type",
    "estimated_amount",
    "title",
    "seace_url",
    "source",
]


def export_opportunities_csv(path: str | Path | None = None) -> Path:
    init_db()
    target = Path(path) if path else settings.results_csv_path
    target.parent.mkdir(parents=True, exist_ok=True)
    rows = _opportunities()

    with target.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=EXPORT_COLUMNS)
        writer.writeheader()
        for item in rows:
            writer.writerow(_row(item))
    return target


def print_opportunities(limit: int = 20, priority: str | None = None) -> None:
    init_db()
    rows = _opportunities(limit=limit, priority=priority)
    if not rows:
        print("No hay oportunidades guardadas.")
        return

    for index, item in enumerate(rows, start=1):
        amount = f"S/ {item.estimated_amount}" if item.estimated_amount else "Monto no indicado"
        print(
            f"{index}. [{item.priority.upper()} | {item.score}] {item.title}\n"
            f"   Entidad: {item.entity_name or 'No indicada'}\n"
            f"   Codigo: {item.seace_code or 'No indicado'} | {amount}\n"
        )


def _opportunities(limit: int | None = None, priority: str | None = None) -> list[Opportunity]:
    priority_rank = case(
        (Opportunity.priority == "alta", 0),
        (Opportunity.priority == "media", 1),
        (Opportunity.priority == "baja", 2),
        (Opportunity.priority == "descartada", 3),
        else_=4,
    )
    stmt = select(Opportunity).order_by(priority_rank, Opportunity.score.desc(), Opportunity.created_at.desc())
    if priority:
        stmt = stmt.where(Opportunity.priority == priority)
    if limit:
        stmt = stmt.limit(limit)
    with SessionLocal() as session:
        return list(session.scalars(stmt).all())


def _row(item: Opportunity) -> dict[str, object]:
    return {
        "priority": item.priority,
        "score": item.score,
        "status": item.status,
        "publication_date": item.publication_date,
        "deadline": item.deadline,
        "entity_name": item.entity_name,
        "seace_code": item.seace_code,
        "object_type": item.object_type,
        "procedure_type": item.procedure_type,
        "estimated_amount": item.estimated_amount,
        "title": item.title,
        "seace_url": item.seace_url,
        "source": item.source,
    }
