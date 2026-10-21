"""Datos de la cuenta y cambio de contraseña."""

import streamlit as st

import database as bd
from traducciones import t, t_error

st.title(t("cuenta_titulo"))
usuario = st.session_state["usuario"]
st.write(t("cuenta_usuario", usuario=usuario))

st.subheader(t("cambiar_contrasena"))
with st.form("form_cambiar_contrasena", clear_on_submit=True):
    actual = st.text_input(t("campo_contrasena_actual"), type="password")
    nueva = st.text_input(
        t("campo_contrasena_nueva"), type="password",
        help=t("ayuda_contrasena", minimo=bd.LARGO_MINIMO_CONTRASENA),
    )
    repetir = st.text_input(t("campo_repetir_nueva"), type="password")
    if st.form_submit_button(t("cambiar_contrasena"), type="primary"):
        if nueva != repetir:
            st.error(t("error_nuevas_no_coinciden"))
        else:
            try:
                bd.cambiar_contrasena(usuario, actual, nueva)
                st.success(t("contrasena_cambiada"))
            except ValueError as error:
                st.error(t_error(error))
