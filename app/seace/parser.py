from __future__ import annotations

from bs4 import BeautifulSoup

from app.utils.text_cleaner import normalize_text


def parse_result_table(html: str, source: str) -> list[dict[str, str]]:
    """Parsea tablas HTML simples exportadas por buscadores públicos.

    El SEACE cambia marcas y vistas con frecuencia; esta función funciona como
    normalizador defensivo para tablas descargadas o páginas renderizadas.
    """
    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict[str, str]] = []
    for table in soup.find_all("table"):
        table_rows = _direct_rows(table)
        if not table_rows:
            continue

        header_index, headers = _headers(table_rows)
        if not headers:
            continue

        for tr in table_rows[header_index + 1 :]:
            cells = tr.find_all("td", recursive=False)
            values = [cell.get_text(" ", strip=True) for cell in cells]
            if _is_data_row(values) and headers:
                item = {headers[i] if i < len(headers) else f"col_{i}": value for i, value in enumerate(values)}
                url = _extract_url(cells)
                if url:
                    item["url"] = url
                item["source"] = source
                rows.append(item)
    return rows


def _direct_rows(table) -> list:
    rows = []
    for section in table.find_all(("thead", "tbody", "tfoot"), recursive=False):
        rows.extend(section.find_all("tr", recursive=False))
    rows.extend(table.find_all("tr", recursive=False))
    return rows


def _headers(rows: list) -> tuple[int, list[str]]:
    for index, row in enumerate(rows):
        cells = row.find_all("th", recursive=False)
        if cells:
            return index, [normalize_text(cell.get_text(" ", strip=True)) for cell in cells]

    first = rows[0] if rows else None
    if not first:
        return 0, []
    cells = first.find_all("td", recursive=False)
    return 0, [normalize_text(cell.get_text(" ", strip=True)) for cell in cells]


def _is_data_row(values: list[str]) -> bool:
    if not values:
        return False
    text = normalize_text(" ".join(values).strip())
    if not text:
        return False
    return "no se encontraron datos" not in text and "sin informacion" not in text


def _extract_url(cells: list) -> str | None:
    for cell in cells:
        for link in cell.find_all("a", href=True):
            href = link.get("href", "").strip()
            if href and href != "#" and not href.lower().startswith("javascript:"):
                return href
    return None
