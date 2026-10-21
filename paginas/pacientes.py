"""Registrar, buscar y editar pacientes."""

from datetime import date

import streamlit as st

import database as bd
from traducciones import preparar_tabla, t, t_error

st.title(t("pacientes_titulo"))

pestana_nuevo, pestana_buscar = st.tabs([t("tab_nuevo_paciente"), t("tab_buscar_editar")])

with pestana_nuevo:
    with st.form("form_nuevo_paciente", clear_on_submit=True):
        col1, col2 = st.columns(2)
        nombre = col1.text_input(t("campo_nombre"))
        apellido = col2.text_input(t("campo_apellido"))
        telefono = col1.text_input(t("campo_telefono"))
        email = col2.text_input(t("campo_email"))
        fecha_nacimiento = col1.date_input(
            t("campo_nacimiento"), value=None, min_value=date(1900, 1, 1), max_value=date.today(),
            format=t("formato_fecha"),
        )
        notas = st.text_area(t("campo_notas"))
        if st.form_submit_button(t("boton_guardar_paciente"), type="primary"):
            try:
                bd.agregar_paciente(nombre, apellido, telefono, email, fecha_nacimiento, notas)
                st.success(t("paciente_guardado", nombre=f"{nombre} {apellido}"))
            except ValueError as error:
                st.error(t_error(error))

with pestana_buscar:
    texto = st.text_input(t("buscar_pacientes"))
    pacientes = bd.buscar_pacientes(texto) if texto else bd.listar_pacientes()

    if pacientes.empty:
        st.info(t("sin_pacientes"))
    else:
        st.dataframe(
            preparar_tabla(
                pacientes[["id", "nombre", "apellido", "telefono", "email", "fecha_nacimiento"]]
            ),
            hide_index=True,
            width="stretch",
        )

        st.subheader(t("editar_paciente"))
        opciones = {
            f"{fila.nombre} {fila.apellido} (#{fila.id})": fila
            for fila in pacientes.itertuples()
        }
        elegido = opciones[st.selectbox(t("campo_paciente"), list(opciones))]

        with st.form("form_editar_paciente"):
            col1, col2 = st.columns(2)
            nombre = col1.text_input(t("campo_nombre"), value=elegido.nombre)
            apellido = col2.text_input(t("campo_apellido"), value=elegido.apellido)
            telefono = col1.text_input(t("campo_telefono"), value=elegido.telefono or "")
            email = col2.text_input(t("campo_email"), value=elegido.email or "")
            nacimiento_actual = (
                date.fromisoformat(elegido.fecha_nacimiento) if elegido.fecha_nacimiento else None
            )
            fecha_nacimiento = col1.date_input(
                t("campo_nacimiento"), value=nacimiento_actual,
                min_value=date(1900, 1, 1), max_value=date.today(), format=t("formato_fecha"),
            )
            notas = st.text_area(t("campo_notas"), value=elegido.notas or "")
            if st.form_submit_button(t("boton_guardar_cambios"), type="primary"):
                try:
                    bd.actualizar_paciente(
                        int(elegido.id), nombre, apellido, telefono, email, fecha_nacimiento, notas
                    )
                    st.success(t("cambios_guardados"))
                    st.rerun()
                except ValueError as error:
                    st.error(t_error(error))
