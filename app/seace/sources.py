from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SeaceSource:
    name: str
    url: str
    description: str


PUBLIC_SOURCES: tuple[SeaceSource, ...] = (
    SeaceSource("procedimientos_seleccion", "https://prod2.seace.gob.pe/seacebus-uiwd-pub/buscadorPublico/buscadorPublico.xhtml", "Procesos ya convocados"),
    SeaceSource("anuncios_contratacion_futura", "https://prod2.seace.gob.pe/seacebus-uiwd-pub/buscadorPublico/buscadorPublico.xhtml", "Oportunidades próximas"),
    SeaceSource("difusion_requerimientos", "https://prod2.seace.gob.pe/seacebus-uiwd-pub/buscadorPublico/buscadorPublico.xhtml", "Requerimientos previos a convocatoria"),
    SeaceSource("condiciones_contratacion", "https://prod2.seace.gob.pe/seacebus-uiwd-pub/buscadorPublico/buscadorPublico.xhtml", "Información preliminar"),
    SeaceSource("ordenes_compra_servicio", "https://prod2.seace.gob.pe/seacebus-uiwd-pub/buscadorPublico/buscadorPublico.xhtml", "Contrataciones menores e histórico"),
    SeaceSource("plan_anual_contrataciones", "https://prod2.seace.gob.pe/seacebus-uiwd-pub/buscadorPublico/buscadorPublico.xhtml", "Posibles oportunidades futuras"),
)
