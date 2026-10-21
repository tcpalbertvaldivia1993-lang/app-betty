"""Registrar y desactivar doctores."""

import streamlit as st

import database as bd
from traducciones import preparar_tabla, t, t_error

st.title(t("doctores_titulo"))

with st.form("form_nuevo_doctor", clear_on_submit=True):
    st.subheader(t("nuevo_doctor"))
    col1, col2, col3 = st.columns(3)
    nombre = col1.text_input(t("campo_nombre_doctor"))
    especialidad = col2.text_input(t("campo_especialidad"))
    telefono = col3.text_input(t("campo_telefono"))
    if st.form_submit_button(t("boton_guardar_doctor"), type="primary"):
        try:
            bd.agregar_doctor(nombre, especialidad, telefono)
            st.success(t("doctor_guardado", nombre=nombre))
        except ValueError as error:
            st.error(t_error(error))

st.subheader(t("lista_doctores"))
mostrar_inactivos = st.checkbox(t("mostrar_inactivos"))
doctores = bd.listar_doctores(solo_activos=not mostrar_inactivos)

if doctores.empty:
    st.info(t("sin_doctores"))
else:
    # "nombre" de un doctor es el nombre completo: se muestra como columna "Doctor"
    st.dataframe(
        preparar_tabla(doctores.rename(columns={"nombre": "doctor"})), hide_index=True, width="stretch"
    )

    activos = doctores[doctores["activo"] == 1]
    if not activos.empty:
        st.subheader(t("desactivar_doctor"))
        st.caption(t("desactivar_doctor_ayuda"))
        opciones = {f"{fila.nombre} - {fila.especialidad}": int(fila.id) for fila in activos.itertuples()}
        elegido = st.selectbox(t("campo_doctor"), list(opciones))
        if st.button(t("boton_desactivar")):
            bd.desactivar_doctor(opciones[elegido])
            st.rerun()
