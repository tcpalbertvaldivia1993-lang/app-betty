"""Registrar, desactivar y reactivar doctores."""

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
doctores = bd.listar_doctores(solo_activos=False)
activos = doctores[doctores["activo"] == 1]
inactivos = doctores[doctores["activo"] == 0]

if doctores.empty:
    st.info(t("sin_doctores"))
else:
    tabla = doctores if mostrar_inactivos else activos
    if tabla.empty:
        st.info(t("sin_doctores_activos"))
    else:
        # "nombre" de un doctor es el nombre completo: se muestra como columna "Doctor"
        st.dataframe(
            preparar_tabla(tabla.rename(columns={"nombre": "doctor"})), hide_index=True, width="stretch"
        )

    col_desactivar, col_reactivar = st.columns(2)

    if not activos.empty:
        with col_desactivar:
            st.subheader(t("desactivar_doctor"))
            st.caption(t("desactivar_doctor_ayuda"))
            opciones = {f"{fila.nombre} - {fila.especialidad}": int(fila.id) for fila in activos.itertuples()}
            elegido = st.selectbox(t("campo_doctor"), list(opciones), key="doctor_desactivar")
            if st.button(t("boton_desactivar")):
                bd.desactivar_doctor(opciones[elegido])
                st.rerun()

    if not inactivos.empty:
        with col_reactivar:
            st.subheader(t("reactivar_doctor"))
            st.caption(t("reactivar_doctor_ayuda"))
            opciones = {f"{fila.nombre} - {fila.especialidad}": int(fila.id) for fila in inactivos.itertuples()}
            elegido = st.selectbox(t("campo_doctor"), list(opciones), key="doctor_reactivar")
            if st.button(t("boton_reactivar")):
                bd.reactivar_doctor(opciones[elegido])
                st.rerun()
