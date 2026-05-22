from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable

from playwright.sync_api import sync_playwright

from app.config.settings import settings
from app.seace.parser import parse_result_table
from app.seace.sources import PUBLIC_SOURCES, SeaceSource
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class SearchQuery:
    keyword: str
    date_from: date | None = None
    date_to: date | None = None
    object_type: str | None = None


class SeaceScraper:
    """Capturador base para buscadores públicos del SEACE.

    No intenta evadir captchas ni automatiza flujos privados con certificado.
    Las implementaciones específicas por fuente pueden extender `_search_source`.
    """

    def __init__(self, headless: bool | None = None) -> None:
        self.headless = settings.seace_headless if headless is None else headless

    def search(self, query: SearchQuery, sources: Iterable[SeaceSource] = PUBLIC_SOURCES) -> list[dict[str, object]]:
        results: list[dict[str, object]] = []
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=self.headless)
            page = browser.new_page()
            try:
                for source in sources:
                    logger.info("Consultando fuente pública SEACE: %s", source.name)
                    results.extend(self._search_source(page, source, query))
            finally:
                browser.close()
        return results

    def _search_source(self, page, source: SeaceSource, query: SearchQuery) -> list[dict[str, object]]:
        page.goto(source.url, wait_until="domcontentloaded", timeout=60000)
        # Punto de extensión: cada buscador público puede tener controles distintos.
        # Por seguridad y mantenibilidad, no se fuerza interacción si aparecen captchas
        # o controles de acceso no públicos.
        html = page.content()
        parsed = parse_result_table(html, source.name)
        return [self._normalize(row, query) for row in parsed]

    @staticmethod
    def _normalize(row: dict[str, str], query: SearchQuery) -> dict[str, object]:
        title = row.get("descripcion") or row.get("objeto") or row.get("nomenclatura") or ""
        return {
            "source": row.get("source", "seace"),
            "seace_code": row.get("nomenclatura") or row.get("codigo") or row.get("código"),
            "title": title,
            "description": row.get("descripcion") or row.get("descripción") or title,
            "entity_name": row.get("entidad"),
            "region": row.get("region") or row.get("región"),
            "object_type": row.get("objeto") or query.object_type,
            "procedure_type": row.get("tipo de procedimiento"),
            "estimated_amount": row.get("valor referencial") or row.get("monto"),
            "publication_date": row.get("fecha de publicacion") or row.get("fecha de publicación"),
            "deadline": row.get("fecha limite") or row.get("fecha límite"),
            "seace_url": row.get("url"),
        }
