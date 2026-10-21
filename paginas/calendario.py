"""Ver las citas por día o semana y estadísticas sencillas."""

from datetime import date, timedelta

import streamlit as st

import database as bd
from traducciones import formatear_fecha, formato_opcion, preparar_tabla, t

st.title(t("calendario_titulo"))

col1, col2, col3 = st.columns(3)
vista = col1.radio(
    t("campo_vista"), ["dia", "semana"], format_func=formato_opcion("vista_"), horizontal=True
)
dia = col2.date_input(t("campo_fecha"), value=date.today(), format=t("formato_fecha"))

doctores = bd.listar_doctores(solo_activos=False)
opciones_doctores = {t("todos"): None} | {
    f"{fila.nombre} ({fila.especialidad})": int(fila.id) for fila in doctores.itertuples()
}
doctor = col3.selectbox(t("campo_doctor"), list(opciones_doctores))

if vista == "dia":
    desde = hasta = dia
else:
    desde = dia - timedelta(days=dia.weekday())  # lunes de esa semana
    hasta = desde + timedelta(days=6)

st.caption(t("rango_fechas", desde=formatear_fecha(desde), hasta=formatear_fecha(hasta)))
citas = bd.citas_por_rango(desde, hasta, opciones_doctores[doctor])

if citas.empty:
    st.info(t("sin_citas_periodo"))
else:
    for fecha, grupo in citas.groupby("fecha"):
        fecha = date.fromisoformat(fecha)
        st.markdown(t(
            "encabezado_dia", dia=t("dias_semana")[fecha.weekday()],
            fecha=formatear_fecha(fecha), cantidad=len(grupo),
        ))
        st.dataframe(
            preparar_tabla(grupo[["hora_inicio", "duracion_min", "paciente", "doctor", "motivo", "estado"]]),
            hide_index=True,
            width="stretch",
        )

st.divider()
st.subheader(t("estadisticas_periodo"))
resumen = bd.estadisticas(desde, hasta)
if resumen.empty:
    st.info(t("sin_datos"))
else:
    # Filas = doctores, columnas = estados (ya traducidos)
    resumen["estado"] = resumen["estado"].map(lambda estado: t(f"estado_{estado}"))
    tabla = resumen.pivot_table(index="doctor", columns="estado", values="total", fill_value=0)
    tabla.index.name = t("col_doctor")
    tabla.columns.name = t("col_estado")
    st.bar_chart(tabla)
    st.dataframe(tabla, width="stretch")
