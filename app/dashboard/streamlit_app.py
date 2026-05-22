from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from app.config.settings import settings
from app.main import run_once

st.set_page_config(page_title="SolarBot SEACE", layout="wide")
st.title("☀️ SolarBot SEACE")
st.caption("Embudo comercial automatizado para oportunidades públicas solares")

latest_csv = Path("data/processed/latest_opportunities.csv")

if "show_results" not in st.session_state:
    st.session_state.show_results = False

with st.sidebar:
    st.subheader("Automatización")
    default_regions = settings.attendable_regions or ["Lima", "Arequipa", "Cusco", "Junin", "Puno"]
    selected_regions = st.multiselect("Regiones para búsqueda", options=default_regions, default=default_regions)
    keyword_input = st.text_area(
        "Palabras clave (una por línea)",
        value="""solar
luminaria solar
panel solar
sistema fotovoltaico""",
        height=140,
    )
    keywords = [line.strip() for line in keyword_input.splitlines() if line.strip()]

    if st.button("Ejecutar búsqueda SEACE ahora", use_container_width=True):
        with st.spinner("Buscando y procesando oportunidades públicas..."):
            processed = run_once(send_telegram=False, keywords=keywords, regions=selected_regions)
        st.success(f"Búsqueda completada. Oportunidades procesadas: {len(processed)}")

    if st.button("Abrir interfaz de resultados", use_container_width=True):
        st.session_state.show_results = True

if latest_csv.exists():
    df = pd.read_csv(latest_csv)
    st.info(f"Mostrando resultados automáticos: {latest_csv}")
else:
    df = pd.DataFrame(columns=["status", "priority", "region", "entity_name", "title", "estimated_amount", "deadline"])
    st.warning("Aún no hay resultados guardados. Define regiones/palabras y ejecuta búsqueda desde la barra lateral.")

if not st.session_state.show_results:
    st.markdown("### Flujo")
    st.write("1) Configura regiones y palabras clave en la barra lateral.")
    st.write("2) Ejecuta búsqueda SEACE.")
    st.write("3) Pulsa **Abrir interfaz de resultados** para revisar lo encontrado.")
else:
    st.subheader("Interfaz de resultados")
    priority = st.multiselect("Prioridad", sorted(df["priority"].dropna().unique()) if not df.empty else [])
    if priority:
        df = df[df["priority"].isin(priority)]

    cols = st.columns(4)
    cols[0].metric("Oportunidades", len(df))
    cols[1].metric("Alta prioridad", int((df.get("priority") == "alta").sum()) if not df.empty else 0)
    cols[2].metric("Monto potencial", f"S/ {pd.to_numeric(df.get('estimated_amount'), errors='coerce').fillna(0).sum():,.2f}" if not df.empty else "S/ 0.00")
    cols[3].metric("Entidades", df.get("entity_name", pd.Series(dtype=str)).nunique() if not df.empty else 0)

    st.subheader("Vista de oportunidades")
    st.dataframe(df, use_container_width=True)

    st.subheader("Kanban por estado")
    statuses = ["nueva", "revisar_bases", "cotizar", "preparar_documentos", "postulada", "ganada", "perdida", "descartada"]
    kanban = st.columns(len(statuses))
    for col, status in zip(kanban, statuses):
        col.markdown(f"**{status.replace('_', ' ').title()}**")
        for _, row in df[df.get("status") == status].head(10).iterrows() if not df.empty else []:
            col.info(f"{row.get('title')}\n\n{row.get('entity_name', '')}")
