from __future__ import annotations

from pathlib import Path

import fitz


def read_pdf_text(path: str | Path) -> str:
    with fitz.open(path) as doc:
        return "\n".join(page.get_text("text") for page in doc)
