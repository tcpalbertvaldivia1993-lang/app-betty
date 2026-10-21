"""Página de inicio: resumen de las citas del día."""

from datetime import date, timedelta

import streamlit as st

import database as bd
from traducciones import formatear_fecha, preparar_tabla, t

st.title(t("inicio_titulo"))
st.caption(t("inicio_ayuda"))

hoy = date.today()
citas_hoy = bd.citas_por_rango(hoy, hoy)

# Métricas del día
col1, col2, col3, col4 = st.columns(4)
col1.metric(t("metrica_citas_hoy"), len(citas_hoy))
col2.metric(t("metrica_pendientes"), int((citas_hoy["estado"] == "programada").sum()))
col3.metric(t("metrica_atendidas"), int((citas_hoy["estado"] == "atendida").sum()))
col4.metric(t("metrica_canceladas"), int((citas_hoy["estado"] == "cancelada").sum()))

st.subheader(t("agenda_hoy", fecha=formatear_fecha(hoy)))
if citas_hoy.empty:
    st.info(t("sin_citas_hoy"))
else:
    st.dataframe(
        preparar_tabla(citas_hoy[["hora_inicio", "paciente", "doctor", "motivo", "estado"]]),
        hide_index=True,
        width="stretch",
    )

st.subheader(t("proximos_7"))
proximas = bd.citas_por_rango(hoy + timedelta(days=1), hoy + timedelta(days=7))
proximas = proximas[proximas["estado"] == "programada"]
if proximas.empty:
    st.info(t("sin_citas_proximas"))
else:
    st.dataframe(
        preparar_tabla(proximas[["fecha", "hora_inicio", "paciente", "doctor", "motivo"]]),
        hide_index=True,
        width="stretch",
    )
