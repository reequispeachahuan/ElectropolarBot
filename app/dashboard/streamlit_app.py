from __future__ import annotations

import pandas as pd
import streamlit as st

st.set_page_config(page_title="SolarBot SEACE", layout="wide")
st.title("☀️ SolarBot SEACE")
st.caption("Embudo comercial para oportunidades públicas solares")

uploaded = st.file_uploader("Cargar oportunidades CSV para revisión", type=["csv"])
if uploaded:
    df = pd.read_csv(uploaded)
else:
    df = pd.DataFrame(columns=["status", "priority", "region", "entity_name", "title", "estimated_amount", "deadline"])

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
