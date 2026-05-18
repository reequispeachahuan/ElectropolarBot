from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from app.config.settings import settings
from app.utils.text_cleaner import compact_slug

SUBFOLDERS = ("bases", "anexos", "propuesta_tecnica", "propuesta_economica", "documentos_empresa")


def build_opportunity_folder(opportunity: dict[str, Any], base_dir: str | Path | None = None) -> Path:
    root = Path(base_dir) if base_dir else settings.data_dir / "opportunities"
    folder_name = "_".join(
        [
            str(date.today()),
            compact_slug(str(opportunity.get("entity_name") or "entidad"), 30),
            compact_slug(str(opportunity.get("title") or "oportunidad"), 40),
        ]
    )
    target = root / folder_name
    target.mkdir(parents=True, exist_ok=True)
    for subfolder in SUBFOLDERS:
        (target / subfolder).mkdir(exist_ok=True)
    return target
