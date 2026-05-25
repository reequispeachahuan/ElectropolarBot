from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
import re
from typing import Iterable
from urllib.parse import quote_plus
from urllib.parse import quote

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright
import requests

from app.config.settings import settings
from app.seace.departments import department_code
from app.seace.parser import parse_result_table
from app.seace.sources import PUBLIC_SOURCES, SeaceSource
from app.utils.logger import get_logger

logger = get_logger(__name__)

RESULT_DATATABLE_BY_SOURCE = {
    "procedimientos_seleccion": "tbBuscador:idFormBuscarProceso:dtProcesos",
    "anuncios_contratacion_futura": "tbBuscador:idFormbuscarACF:dtResultadosACF",
}
DEPARTMENT_FILTER_SOURCES = {"procedimientos_seleccion"}


@dataclass(frozen=True)
class SearchQuery:
    keyword: str
    department: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    object_type: str | None = None


class SeaceScraper:
    """Base scraper for public SEACE pages.

    It does not bypass captchas and does not automate private certificate-based
    flows. Source-specific interactions can extend `_search_source`.
    """

    def __init__(self, headless: bool | None = None) -> None:
        self.headless = settings.seace_headless if headless is None else headless

    def search(self, query: SearchQuery, sources: Iterable[SeaceSource] = PUBLIC_SOURCES) -> list[dict[str, object]]:
        if settings.seace_source.lower() == "openegocio":
            return self._search_openegocio(query)

        results: list[dict[str, object]] = []
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=self.headless)
            page = browser.new_page(
                viewport={"width": 1366, "height": 768},
                user_agent=(
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                ),
            )
            page.set_default_timeout(45000)
            try:
                for source in sources:
                    logger.info("Consultando fuente publica SEACE: %s", source.name)
                    try:
                        results.extend(self._search_source(page, source, query))
                    except Exception:
                        self._save_debug_artifacts(page, source.name)
                        logger.exception("No se pudo consultar fuente SEACE: %s", source.name)
            finally:
                browser.close()
        return results

    def _search_openegocio(self, query: SearchQuery) -> list[dict[str, object]]:
        results: list[dict[str, object]] = []
        department = department_code(query.department)
        keyword = quote(query.keyword or "0", safe="")
        for object_code in settings.seace_object_codes:
            url = (
                f"{settings.seace_openegocio_base_url.rstrip('/')}"
                f"/codObjeto/codDepartamento/sintesisProceso/codTipoProceso/"
                f"{object_code}/{department}/{keyword}/0"
            )
            logger.info(
                "Consultando SEACE Oportunidades de Negocio: objeto=%s departamento=%s keyword=%s",
                object_code,
                query.department or "todos",
                query.keyword,
            )
            response = requests.get(
                url,
                timeout=60,
                headers={
                    "Accept": "application/json",
                    "User-Agent": (
                        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                    ),
                },
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, list):
                logger.warning("Respuesta SEACE prod4 inesperada para %s: %s", url, type(payload).__name__)
                continue
            results.extend(self._normalize_openegocio_row(item, query) for item in payload if isinstance(item, dict))
        return [item for item in results if self._has_identity(item)]

    def _search_source(self, page, source: SeaceSource, query: SearchQuery) -> list[dict[str, object]]:
        if query.department and source.name not in DEPARTMENT_FILTER_SOURCES:
            logger.info("Se omite %s porque no expone filtro de departamento", source.name)
            return []
        page.goto(source.url, wait_until="domcontentloaded", timeout=60000)
        try:
            page.wait_for_selector("id=tbBuscador", timeout=45000)
        except PlaywrightTimeoutError as exc:
            raise RuntimeError(f"SEACE no cargo el buscador publico. URL final: {page.url}") from exc
        self._apply_search(page, source, query)
        return self._collect_paginated_results(page, source, query)

    def _collect_paginated_results(self, page, source: SeaceSource, query: SearchQuery) -> list[dict[str, object]]:
        datatable_id = RESULT_DATATABLE_BY_SOURCE.get(source.name)
        results: list[dict[str, object]] = []
        page_count = self._page_count(page, datatable_id)
        for index in range(page_count):
            logger.info("Parseando %s pagina %s/%s", source.name, index + 1, page_count)
            results.extend(self._parse_current_results(page, source, query, datatable_id))
            if index + 1 >= page_count:
                break
            if not self._advance_page(page, datatable_id):
                break
        return results

    def _parse_current_results(
        self,
        page,
        source: SeaceSource,
        query: SearchQuery,
        datatable_id: str | None,
    ) -> list[dict[str, object]]:
        html = self._result_html(page, datatable_id)
        parsed = parse_result_table(html, source.name)
        normalized = [self._normalize(row, query) for row in parsed]
        results = [item for item in normalized if self._has_identity(item)]
        if settings.seace_capture_detail_urls and source.name == "procedimientos_seleccion":
            detail_urls = self._capture_detail_urls(page, datatable_id)
            for item, detail_url in zip(results, detail_urls):
                if detail_url:
                    item["seace_url"] = detail_url
        return results

    @staticmethod
    def _result_html(page, datatable_id: str | None) -> str:
        if not datatable_id:
            return page.content()
        locator = page.locator(f"id={datatable_id}")
        if locator.count() == 0:
            return page.content()
        return locator.first.evaluate("(element) => element.outerHTML")

    def _apply_search(self, page, source: SeaceSource, query: SearchQuery) -> None:
        if source.name == "procedimientos_seleccion":
            self._search_procedimientos_seleccion(page, query)
            return
        if source.name == "anuncios_contratacion_futura":
            self._search_anuncios_contratacion_futura(page, query)
            return

    def _search_procedimientos_seleccion(self, page, query: SearchQuery) -> None:
        description_selector = "id=tbBuscador:idFormBuscarProceso:descripcionObjeto"
        self._show_tab(page, "#tbBuscador:tab1", description_selector, "procedimientos de seleccion")
        self._fill_input(page, description_selector, query.keyword)
        if query.department:
            self._select_primefaces_option_by_label(
                page,
                "id=tbBuscador:idFormBuscarProceso:departamento_input",
                query.department,
            )
        self._click_and_wait(page, "id=tbBuscador:idFormBuscarProceso:btnBuscarSelToken")

    def _search_anuncios_contratacion_futura(self, page, query: SearchQuery) -> None:
        description_selector = "id=tbBuscador:idFormbuscarACF:descripcionObjeto"
        self._show_tab(page, "#tbBuscador:tab7", description_selector, "anuncios de contratacion futura")
        self._fill_input(page, description_selector, query.keyword)
        self._click_and_wait(page, "id=tbBuscador:idFormbuscarACF:btnBuscarSelCCOToken")

    @staticmethod
    def _show_tab(page, tab_href: str, ready_selector: str, tab_name: str) -> None:
        ready = page.locator(ready_selector).first
        try:
            ready.wait_for(state="visible", timeout=5000)
            return
        except PlaywrightTimeoutError:
            pass

        tab = page.locator(f'a[href$="{tab_href}"]').first
        if tab.count() > 0:
            try:
                tab.click(force=True, timeout=10000)
            except PlaywrightTimeoutError:
                logger.warning("No se pudo abrir pestana SEACE: %s", tab_name)
        else:
            logger.warning("No se encontro pestana SEACE: %s; se buscara formulario directo", tab_name)

        if page.locator(ready_selector).count() == 0:
            page.evaluate(
                """(href) => {
                    const link = Array.from(document.querySelectorAll("a"))
                        .find((item) => item.getAttribute("href") === href);
                    if (link) {
                        link.click();
                    }
                }""",
                tab_href,
            )

        page.evaluate(
            """(href) => {
                const panelId = href.replace(/^#/, "");
                const panel = document.getElementById(panelId);
                if (panel) {
                    panel.style.display = "block";
                    panel.setAttribute("aria-hidden", "false");
                }
            }""",
            tab_href,
        )

        try:
            ready.wait_for(state="visible", timeout=15000)
        except PlaywrightTimeoutError as exc:
            if page.locator(ready_selector).count() > 0:
                logger.warning("Formulario SEACE de %s existe pero no esta visible; se llenara por DOM", tab_name)
                return
            raise RuntimeError(f"No se encontro formulario SEACE para {tab_name}. URL final: {page.url}") from exc

    @staticmethod
    def _fill_input(page, selector: str, value: str) -> None:
        locator = page.locator(selector)
        if locator.count() == 0:
            raise RuntimeError(f"No se encontro selector SEACE: {selector}")
        try:
            locator.first.fill(value, timeout=10000)
        except PlaywrightTimeoutError:
            locator.first.evaluate(
                """(input, text) => {
                    input.value = text;
                    input.dispatchEvent(new Event("input", { bubbles: true }));
                    input.dispatchEvent(new Event("change", { bubbles: true }));
                }""",
                value,
            )

    @staticmethod
    def _click_and_wait(page, selector: str) -> None:
        page.locator(selector).click(force=True)
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except PlaywrightTimeoutError:
            logger.warning("SEACE no quedo en networkidle luego de buscar; se parsea el HTML disponible")
        page.wait_for_timeout(3000)

    @staticmethod
    def _select_primefaces_option_by_label(page, selector: str, label: str) -> None:
        locator = page.locator(selector)
        if locator.count() == 0:
            raise RuntimeError(f"No se encontro selector SEACE: {selector}")
        selected = locator.first.evaluate(
            """(select, wanted) => {
                const normalize = (value) => (value || "")
                    .normalize("NFD")
                    .replace(/[\\u0300-\\u036f]/g, "")
                    .trim()
                    .toUpperCase();
                const option = Array.from(select.options).find(
                    (item) => normalize(item.textContent) === normalize(wanted)
                );
                if (!option) {
                    return null;
                }
                select.value = option.value;
                select.dispatchEvent(new Event("change", { bubbles: true }));
                return option.textContent.trim();
            }""",
            label,
        )
        if not selected:
            raise ValueError(f"No se encontro opcion SEACE '{label}' en {selector}")
        logger.info("Filtro SEACE seleccionado: %s", selected)

    def _page_count(self, page, datatable_id: str | None) -> int:
        if not datatable_id:
            return 1
        paginator = page.locator(f"id={datatable_id}_paginator_bottom")
        if paginator.count() == 0:
            return 1
        current = paginator.first.locator(".ui-paginator-current").first
        text = current.inner_text() if current.count() else ""
        page_count = self._page_count_from_text(text)
        if settings.seace_max_pages > 0:
            return min(page_count, settings.seace_max_pages)
        return page_count

    @staticmethod
    def _page_count_from_text(text: str) -> int:
        match = re.search(r"\b\d+\s*/\s*(\d+)\b", text)
        if match:
            return max(1, int(match.group(1)))
        match = re.search(r"\b\d+\s+de\s+(\d+)\b", text.lower())
        if match:
            return max(1, int(match.group(1)))
        return 1

    @staticmethod
    def _advance_page(page, datatable_id: str | None) -> bool:
        if not datatable_id:
            return False
        paginator = page.locator(f"id={datatable_id}_paginator_bottom")
        if paginator.count() == 0:
            return False
        next_button = paginator.first.locator(".ui-paginator-next").first
        if next_button.count() == 0:
            return False
        class_name = next_button.get_attribute("class") or ""
        if "ui-state-disabled" in class_name:
            return False
        next_button.click(force=True)
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except PlaywrightTimeoutError:
            logger.warning("SEACE no quedo en networkidle luego de avanzar pagina")
        page.wait_for_timeout(2500)
        return True

    @staticmethod
    def _capture_detail_urls(page, datatable_id: str | None) -> list[str | None]:
        if not datatable_id:
            return []
        rows = page.locator(f"id={datatable_id}_data").locator("tr")
        urls: list[str | None] = []
        for index in range(rows.count()):
            row = rows.nth(index)
            link = row.locator('img[id$="grafichaSel"]').locator("xpath=ancestor::a[1]")
            if link.count() == 0:
                urls.append(None)
                continue
            try:
                link.first.click(force=True)
                page.wait_for_timeout(1500)
                urls.append(page.url)
                page.go_back(wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(1500)
            except Exception:
                logger.exception("No se pudo capturar URL directa SEACE para fila %s", index + 1)
                urls.append(None)
        return urls

    @staticmethod
    def _normalize(row: dict[str, str], query: SearchQuery) -> dict[str, object]:
        title = (
            row.get("descripcion")
            or row.get("descripcion del objeto")
            or row.get("descripcion de objeto")
            or row.get("descripcion del objeto de contratacion")
            or row.get("objeto")
            or row.get("nomenclatura")
            or ""
        )
        return {
            "source": row.get("source", "seace"),
            "seace_code": row.get("nomenclatura") or row.get("codigo") or row.get("codigo unico de inversion"),
            "title": title,
            "description": (
                row.get("descripcion")
                or row.get("descripcion del objeto")
                or row.get("descripcion de objeto")
                or row.get("descripcion del objeto de contratacion")
                or title
            ),
            "entity_name": row.get("entidad") or row.get("nombre o sigla de la entidad"),
            "region": row.get("region") or row.get("departamento") or query.department,
            "object_type": row.get("objeto") or row.get("objeto de contratacion") or query.object_type,
            "procedure_type": row.get("tipo de procedimiento") or row.get("tipo de seleccion"),
            "estimated_amount": row.get("valor referencial") or row.get("monto") or row.get("vr / ve / cuantia de la contratacion"),
            "publication_date": row.get("fecha de publicacion") or row.get("fecha y hora de publicacion"),
            "deadline": row.get("fecha limite"),
            "seace_url": row.get("url") or SeaceScraper._fallback_search_url(row.get("nomenclatura")),
        }

    @staticmethod
    def _has_identity(opportunity: dict[str, object]) -> bool:
        return any(opportunity.get(key) for key in ("seace_code", "title", "description"))

    @staticmethod
    def _fallback_search_url(seace_code: str | None) -> str:
        base_url = "https://prod2.seace.gob.pe/seacebus-uiwd-pub/buscadorPublico/buscadorPublico.xhtml"
        if not seace_code:
            return base_url
        return f"{base_url}#buscar:{quote_plus(seace_code)}"

    @staticmethod
    def _normalize_openegocio_row(row: dict[str, object], query: SearchQuery) -> dict[str, object]:
        title = _first_text(row, "detItem", "sintesisProceso", "detCubso", "nomenclatura")
        description_parts = [
            _first_text(row, "sintesisProceso"),
            _first_text(row, "detItem"),
            _first_text(row, "detCubso"),
        ]
        description = " | ".join(part for part in description_parts if part)
        nomenclature = _first_text(row, "nomenclatura")
        item = _first_text(row, "nroItem")
        seace_code = "#".join(part for part in (nomenclature, item) if part)
        id_procedure = _first_text(row, "idProcedimiento")
        seace_url = (
            f"https://prod4.seace.gob.pe/openegocio/#/ficha/idProceso/{id_procedure}"
            if id_procedure
            else "https://prod4.seace.gob.pe/openegocio/"
        )
        return {
            "source": "seace_oportunidades_negocio",
            "seace_code": seace_code or id_procedure,
            "title": title,
            "description": description or title,
            "entity_name": _first_text(row, "detEntidad"),
            "region": query.department,
            "object_type": _first_text(row, "detObjeto"),
            "procedure_type": _first_text(row, "detTipoProceso"),
            "estimated_amount": _first_text(row, "valorReferencialItem", "valorReferencial"),
            "publication_date": _first_text(row, "fechaConvocatoria"),
            "deadline": _first_text(row, "fechaFin", "fechaPresentacionPropuestas"),
            "seace_url": seace_url,
        }

    @staticmethod
    def _save_debug_artifacts(page, source_name: str) -> None:
        debug_dir = settings.data_dir / "debug"
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        safe_source = re.sub(r"[^a-zA-Z0-9_-]+", "_", source_name)
        html_path = debug_dir / f"seace_{safe_source}_{timestamp}.html"
        screenshot_path = debug_dir / f"seace_{safe_source}_{timestamp}.png"
        try:
            debug_dir.mkdir(parents=True, exist_ok=True)
            html_path.write_text(page.content(), encoding="utf-8")
            page.screenshot(path=str(screenshot_path), full_page=True)
            logger.error(
                "Diagnostico SEACE guardado: html=%s screenshot=%s url=%s title=%s",
                html_path,
                screenshot_path,
                page.url,
                page.title(),
            )
        except Exception:
            logger.exception("No se pudo guardar diagnostico SEACE")


def _first_text(row: dict[str, object], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text and text != "---":
            return text
    return ""
