from __future__ import annotations

from bs4 import BeautifulSoup


def parse_result_table(html: str, source: str) -> list[dict[str, str]]:
    """Parsea tablas HTML simples exportadas por buscadores públicos.

    El SEACE cambia marcas y vistas con frecuencia; esta función funciona como
    normalizador defensivo para tablas descargadas o páginas renderizadas.
    """
    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict[str, str]] = []
    for table in soup.find_all("table"):
        headers = [cell.get_text(" ", strip=True).lower() for cell in table.find_all("th")]
        if not headers:
            first = table.find("tr")
            headers = [cell.get_text(" ", strip=True).lower() for cell in first.find_all("td")] if first else []
        for tr in table.find_all("tr")[1:]:
            values = [cell.get_text(" ", strip=True) for cell in tr.find_all("td")]
            if values and headers:
                item = {headers[i] if i < len(headers) else f"col_{i}": value for i, value in enumerate(values)}
                item["source"] = source
                rows.append(item)
    return rows
