from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from app.main import run_once

st.set_page_config(page_title="SolarBot SEACE", layout="wide")
st.title("☀️ SolarBot SEACE")
st.caption("Embudo comercial automatizado para oportunidades públicas solares")

latest_csv = Path("data/processed/latest_opportunities.csv")

with st.sidebar:
    st.subheader("Automatización")
    if st.button("Ejecutar búsqueda SEACE ahora", use_container_width=True):
        with st.spinner("Buscando y procesando oportunidades públicas..."):
            processed = run_once(send_telegram=False)
        st.success(f"Búsqueda completada. Oportunidades procesadas: {len(processed)}")

if latest_csv.exists():
    df = pd.read_csv(latest_csv)
    st.info(f"Mostrando resultados automáticos: {latest_csv}")
else:
    df = pd.DataFrame(columns=["status", "priority", "region", "entity_name", "title", "estimated_amount", "deadline"])
    st.warning("Aún no hay resultados guardados. Ejecuta una búsqueda desde el botón lateral o por CLI.")

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
