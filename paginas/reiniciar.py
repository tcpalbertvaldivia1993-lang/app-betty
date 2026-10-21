"""Borrar todos los doctores, pacientes y citas para empezar de cero (solo administradores)."""

import streamlit as st

import database as bd
from traducciones import t

st.title(t("reiniciar_titulo"))

# Defensa extra: app.py ya oculta esta página al personal
yo = bd.obtener_usuario(st.session_state["usuario"])
if yo["rol"] != "administrador":
    st.error(t("solo_admin"))
    st.stop()

# Mensaje del reinicio anterior (se guarda antes de recargar la página)
if "mensaje_reinicio" in st.session_state:
    st.success(st.session_state.pop("mensaje_reinicio"))

st.write(t("reiniciar_explicacion"))

conteos = bd.contar_datos()
col1, col2, col3 = st.columns(3)
col1.metric(t("pag_doctores"), conteos["doctores"])
col2.metric(t("pag_pacientes"), conteos["pacientes"])
col3.metric(t("pag_citas"), conteos["citas"])

if sum(conteos.values()) == 0:
    st.info(t("sin_datos_que_borrar"))
    st.stop()

st.warning(t("reiniciar_advertencia"))

# Dos confirmaciones, porque borrar todo es muy fácil de hacer por error
entiendo = st.checkbox(t("reiniciar_entiendo"))
palabra = t("palabra_confirmar")
escrito = st.text_input(t("reiniciar_escribe", palabra=palabra))
confirmado = entiendo and escrito.strip().upper() == palabra

if st.button(t("boton_reiniciar"), type="primary", disabled=not confirmado):
    respaldo, borrados = bd.reiniciar_datos()
    st.session_state["mensaje_reinicio"] = t(
        "reinicio_hecho", doctores=borrados["doctores"], pacientes=borrados["pacientes"],
        citas=borrados["citas"], respaldo=f"respaldos/{respaldo.name}",
    )
    st.rerun()
