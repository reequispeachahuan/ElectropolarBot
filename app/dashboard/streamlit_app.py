from __future__ import annotations

import pandas as pd
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
import streamlit as st

from app.database.models import Opportunity, ScanRun
from app.database.repository import update_opportunity_status
from app.database.session import SessionLocal, init_db

STATUSES = ["nueva", "revisar_bases", "cotizar", "preparar_documentos", "postulada", "ganada", "perdida", "descartada"]
DEFAULT_COLUMNS = [
    "id",
    "status",
    "priority",
    "region",
    "entity_name",
    "title",
    "estimated_amount",
    "deadline",
    "score",
    "seace_code",
    "seace_url",
]


@st.cache_data(ttl=60)
def _load_opportunities() -> pd.DataFrame:
    init_db()
    try:
        with SessionLocal() as session:
            rows = session.scalars(select(Opportunity).order_by(Opportunity.created_at.desc())).all()
    except SQLAlchemyError as exc:
        st.warning(f"No se pudo conectar a la base de datos: {exc}")
        return pd.DataFrame(columns=DEFAULT_COLUMNS)

    return pd.DataFrame(
        [
            {
                "id": item.id,
                "status": item.status,
                "priority": item.priority,
                "region": item.region,
                "entity_name": item.entity_name,
                "title": item.title,
                "estimated_amount": float(item.estimated_amount or 0),
                "deadline": item.deadline,
                "score": item.score,
                "seace_code": item.seace_code,
                "seace_url": item.seace_url,
            }
            for item in rows
        ],
        columns=DEFAULT_COLUMNS,
    )


@st.cache_data(ttl=60)
def _load_runs() -> pd.DataFrame:
    init_db()
    try:
        with SessionLocal() as session:
            rows = session.scalars(select(ScanRun).order_by(ScanRun.started_at.desc()).limit(20)).all()
    except SQLAlchemyError:
        return pd.DataFrame()
    return pd.DataFrame(
        [
            {
                "started_at": item.started_at,
                "status": item.status,
                "keywords": item.keywords,
                "departments": item.departments,
                "processed": item.processed_count,
                "alta": item.high_count,
                "media": item.medium_count,
                "baja": item.low_count,
                "descartada": item.discarded_count,
                "alerts_sent": item.alerts_sent,
                "alerts_failed": item.alerts_failed,
                "error": item.error_message,
            }
            for item in rows
        ]
    )


def _update_status(opportunity_id: str, status: str) -> bool:
    with SessionLocal() as session:
        return update_opportunity_status(session, opportunity_id, status)


st.set_page_config(page_title="SolarBot SEACE", layout="wide")
st.title("SolarBot SEACE")
st.caption("Embudo comercial para oportunidades publicas solares")

uploaded = st.sidebar.file_uploader("Cargar oportunidades CSV", type=["csv"])
if uploaded:
    df = pd.read_csv(uploaded)
else:
    df = _load_opportunities()

for column in DEFAULT_COLUMNS:
    if column not in df.columns:
        df[column] = None

priority = st.sidebar.multiselect("Prioridad", sorted(df["priority"].dropna().unique()) if not df.empty else [])
status_filter = st.sidebar.multiselect("Estado", STATUSES)
if priority:
    df = df[df["priority"].isin(priority)]
if status_filter:
    df = df[df["status"].isin(status_filter)]

cols = st.columns(4)
cols[0].metric("Oportunidades", len(df))
cols[1].metric("Alta prioridad", int((df.get("priority") == "alta").sum()) if not df.empty else 0)
cols[2].metric(
    "Monto potencial",
    f"S/ {pd.to_numeric(df.get('estimated_amount'), errors='coerce').fillna(0).sum():,.2f}"
    if not df.empty
    else "S/ 0.00",
)
cols[3].metric("Entidades", df.get("entity_name", pd.Series(dtype=str)).nunique() if not df.empty else 0)

st.subheader("Actualizar estado")
if df.empty or uploaded:
    st.info("Carga datos desde la base para cambiar estados.")
else:
    options = {
        f"{row.seace_code or row.id} | {row.priority.upper()} | {str(row.title)[:90]}": row.id
        for row in df.itertuples()
    }
    selected = st.selectbox("Oportunidad", list(options.keys()))
    next_status = st.selectbox("Nuevo estado", STATUSES)
    if st.button("Guardar estado", type="primary"):
        if _update_status(options[selected], next_status):
            st.cache_data.clear()
            st.success("Estado actualizado")
            st.rerun()
        else:
            st.error("No se encontro la oportunidad")

st.subheader("Vista de oportunidades")
visible_columns = [column for column in DEFAULT_COLUMNS if column != "id"]
st.dataframe(df[visible_columns], width="stretch")

st.subheader("Kanban por estado")
kanban = st.columns(len(STATUSES))
for col, status in zip(kanban, STATUSES):
    col.markdown(f"**{status.replace('_', ' ').title()}**")
    for _, row in df[df.get("status") == status].head(8).iterrows() if not df.empty else []:
        col.info(f"{row.get('title')}\n\n{row.get('entity_name', '')}")

st.subheader("Ultimas corridas")
runs = _load_runs()
if runs.empty:
    st.caption("Sin corridas registradas.")
else:
    st.dataframe(runs, width="stretch")
