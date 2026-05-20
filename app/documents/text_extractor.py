from __future__ import annotations

from pathlib import Path

from app.documents.pdf_reader import read_pdf_text


def extract_text(path: str | Path) -> str:
    file_path = Path(path)
    if file_path.suffix.lower() == ".pdf":
        return read_pdf_text(file_path)
    if file_path.suffix.lower() in {".txt", ".md"}:
        return file_path.read_text(encoding="utf-8")
    raise ValueError(f"Formato no soportado todavía: {file_path.suffix}")
