from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SeaceSource:
    name: str
    url: str
    description: str


PUBLIC_SOURCES: tuple[SeaceSource, ...] = (
    SeaceSource(
        "procedimientos_seleccion",
        "https://prod2.seace.gob.pe/",
        "Buscador de Procedimientos de Seleccion",
    ),
    SeaceSource(
        "anuncios_contratacion_futura",
        "https://prod2.seace.gob.pe/",
        "Anuncios de Contratacion Futura",
    ),
)
