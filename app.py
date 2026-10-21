"""Página de inicio de la app de citas de la clínica.

Ejecutar con:  .venv/bin/streamlit run app.py
"""

from datetime import date, timedelta

import streamlit as st

import database as bd

st.set_page_config(page_title="Clínica - Citas", page_icon="🏥", layout="wide")
bd.crear_tablas()

st.title("🏥 Citas de la clínica")
st.caption("Usa el menú de la izquierda para gestionar pacientes, doctores y citas.")

hoy = date.today()
citas_hoy = bd.citas_por_rango(hoy, hoy)

# Métricas del día
col1, col2, col3, col4 = st.columns(4)
col1.metric("Citas hoy", len(citas_hoy))
col2.metric("Pendientes", int((citas_hoy["estado"] == "programada").sum()))
col3.metric("Atendidas", int((citas_hoy["estado"] == "atendida").sum()))
col4.metric("Canceladas", int((citas_hoy["estado"] == "cancelada").sum()))

st.subheader(f"Agenda de hoy ({hoy:%d/%m/%Y})")
if citas_hoy.empty:
    st.info("No hay citas para hoy.")
else:
    st.dataframe(
        citas_hoy[["hora_inicio", "paciente", "doctor", "motivo", "estado"]],
        hide_index=True,
        width="stretch",
    )

st.subheader("Próximos 7 días")
proximas = bd.citas_por_rango(hoy + timedelta(days=1), hoy + timedelta(days=7))
proximas = proximas[proximas["estado"] == "programada"]
if proximas.empty:
    st.info("No hay citas programadas para los próximos días.")
else:
    st.dataframe(
        proximas[["fecha", "hora_inicio", "paciente", "doctor", "motivo"]],
        hide_index=True,
        width="stretch",
    )
