"""Ver las citas por día o semana y estadísticas sencillas."""

from datetime import date, timedelta

import streamlit as st

import database as bd

st.title("🗓️ Calendario y reportes")

col1, col2, col3 = st.columns(3)
vista = col1.radio("Vista", ["Día", "Semana"], horizontal=True)
dia = col2.date_input("Fecha", value=date.today(), format="DD/MM/YYYY")

doctores = bd.listar_doctores(solo_activos=False)
opciones_doctores = {"Todos": None} | {
    f"{fila.nombre} ({fila.especialidad})": int(fila.id) for fila in doctores.itertuples()
}
doctor = col3.selectbox("Doctor", list(opciones_doctores))

if vista == "Día":
    desde = hasta = dia
else:
    desde = dia - timedelta(days=dia.weekday())  # lunes de esa semana
    hasta = desde + timedelta(days=6)

st.caption(f"Del {desde:%d/%m/%Y} al {hasta:%d/%m/%Y}")
citas = bd.citas_por_rango(desde, hasta, opciones_doctores[doctor])

if citas.empty:
    st.info("No hay citas en este periodo.")
else:
    for fecha, grupo in citas.groupby("fecha"):
        st.markdown(f"**{date.fromisoformat(fecha):%A %d/%m/%Y}** — {len(grupo)} cita(s)")
        st.dataframe(
            grupo[["hora_inicio", "duracion_min", "paciente", "doctor", "motivo", "estado"]],
            hide_index=True,
            width="stretch",
        )

st.divider()
st.subheader("Estadísticas del periodo")
resumen = bd.estadisticas(desde, hasta)
if resumen.empty:
    st.info("Sin datos para mostrar.")
else:
    # Filas = doctores, columnas = estados
    tabla = resumen.pivot_table(index="doctor", columns="estado", values="total", fill_value=0)
    st.bar_chart(tabla)
    st.dataframe(tabla, width="stretch")
