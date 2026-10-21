"""Registrar y desactivar doctores."""

import streamlit as st

import database as bd

st.set_page_config(page_title="Doctores", page_icon="🩺", layout="wide")
bd.crear_tablas()
st.title("🩺 Doctores")

with st.form("form_nuevo_doctor", clear_on_submit=True):
    st.subheader("Nuevo doctor")
    col1, col2, col3 = st.columns(3)
    nombre = col1.text_input("Nombre *")
    especialidad = col2.text_input("Especialidad *")
    telefono = col3.text_input("Teléfono")
    if st.form_submit_button("Guardar doctor", type="primary"):
        try:
            bd.agregar_doctor(nombre, especialidad, telefono)
            st.success(f"{nombre} guardado.")
        except ValueError as error:
            st.error(str(error))

st.subheader("Lista de doctores")
mostrar_inactivos = st.checkbox("Mostrar también los inactivos")
doctores = bd.listar_doctores(solo_activos=not mostrar_inactivos)

if doctores.empty:
    st.info("Todavía no hay doctores registrados.")
else:
    tabla = doctores.copy()
    tabla["activo"] = tabla["activo"].map({1: "Sí", 0: "No"})
    st.dataframe(tabla, hide_index=True, width="stretch")

    activos = doctores[doctores["activo"] == 1]
    if not activos.empty:
        st.subheader("Desactivar doctor")
        st.caption("El doctor deja de aparecer al agendar citas, pero se conservan sus citas anteriores.")
        opciones = {f"{fila.nombre} - {fila.especialidad}": int(fila.id) for fila in activos.itertuples()}
        elegido = st.selectbox("Doctor", list(opciones))
        if st.button("Desactivar"):
            bd.desactivar_doctor(opciones[elegido])
            st.rerun()
