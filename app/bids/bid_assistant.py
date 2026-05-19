from __future__ import annotations

from pathlib import Path
from typing import Any

from app.bids.checklist import render_checklist
from app.bids.folder_builder import build_opportunity_folder
from app.documents.summary_generator import generate_executive_summary


class BidAssistant:
    def prepare_workspace(self, opportunity: dict[str, Any], base_dir: str | Path | None = None) -> Path:
        folder = build_opportunity_folder(opportunity, base_dir)
        (folder / "checklist.md").write_text(render_checklist(), encoding="utf-8")
        (folder / "resumen.md").write_text(generate_executive_summary(opportunity), encoding="utf-8")
        return folder
