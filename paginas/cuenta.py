"""Datos de la cuenta y cambio de contraseña."""

import streamlit as st

import database as bd

st.title("🔑 Mi cuenta")
usuario = st.session_state["usuario"]
st.write(f"Usuario: **{usuario}**")

st.subheader("Cambiar contraseña")
with st.form("form_cambiar_contrasena", clear_on_submit=True):
    actual = st.text_input("Contraseña actual", type="password")
    nueva = st.text_input(
        "Contraseña nueva", type="password",
        help=f"Mínimo {bd.LARGO_MINIMO_CONTRASENA} caracteres.",
    )
    repetir = st.text_input("Repite la contraseña nueva", type="password")
    if st.form_submit_button("Cambiar contraseña", type="primary"):
        if nueva != repetir:
            st.error("Las contraseñas nuevas no coinciden.")
        else:
            try:
                bd.cambiar_contrasena(usuario, actual, nueva)
                st.success("Contraseña cambiada. Úsala la próxima vez que inicies sesión.")
            except ValueError as error:
                st.error(str(error))
