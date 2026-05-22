from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SeaceSource:
    name: str
    url: str
    description: str


PUBLIC_SOURCES: tuple[SeaceSource, ...] = (
    SeaceSource("procedimientos_seleccion", "https://prodapp.seace.gob.pe/portal/", "Procesos ya convocados"),
    SeaceSource("anuncios_contratacion_futura", "https://prodapp.seace.gob.pe/portal/", "Oportunidades próximas"),
    SeaceSource("difusion_requerimientos", "https://prodapp.seace.gob.pe/portal/", "Requerimientos previos a convocatoria"),
    SeaceSource("condiciones_contratacion", "https://prodapp.seace.gob.pe/portal/", "Información preliminar"),
    SeaceSource("ordenes_compra_servicio", "https://prodapp.seace.gob.pe/portal/", "Contrataciones menores e histórico"),
    SeaceSource("plan_anual_contrataciones", "https://prodapp.seace.gob.pe/portal/", "Posibles oportunidades futuras"),
)
