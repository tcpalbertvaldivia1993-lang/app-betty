"""Entrada de la app de citas de la clínica.

Ejecutar con:  .venv/bin/streamlit run app.py

Antes de mostrar cualquier página pide usuario y contraseña.
La primera vez que se abre, pide crear la cuenta del administrador (el propietario).
"""

import streamlit as st

import database as bd

st.set_page_config(page_title="Clínica - Citas", page_icon="🏥", layout="wide")
bd.crear_tablas()


def pantalla_crear_administrador():
    """Se muestra solo la primera vez, cuando todavía no hay ningún usuario."""
    st.title("🏥 Bienvenido")
    st.write("Es la primera vez que se abre la app. Crea la cuenta del administrador (propietario de la clínica).")
    with st.form("form_crear_administrador"):
        usuario = st.text_input("Usuario")
        contrasena = st.text_input(
            "Contraseña", type="password",
            help=f"Mínimo {bd.LARGO_MINIMO_CONTRASENA} caracteres.",
        )
        repetir = st.text_input("Repite la contraseña", type="password")
        if st.form_submit_button("Crear administrador", type="primary"):
            if contrasena != repetir:
                st.error("Las contraseñas no coinciden.")
            else:
                try:
                    bd.crear_usuario(usuario, contrasena)
                    st.session_state["usuario"] = usuario.strip()
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))


def pantalla_login():
    st.title("🔒 Iniciar sesión")
    with st.form("form_login"):
        usuario = st.text_input("Usuario")
        contrasena = st.text_input("Contraseña", type="password")
        if st.form_submit_button("Entrar", type="primary"):
            if bd.verificar_usuario(usuario, contrasena):
                st.session_state["usuario"] = usuario.strip()
                st.rerun()
            else:
                # No se dice cuál de los dos falló, para no dar pistas
                st.error("Usuario o contraseña incorrectos.")


if "usuario" not in st.session_state:
    # Sin sesión: la única página disponible es la de acceso
    if bd.hay_usuarios():
        pagina = st.navigation([st.Page(pantalla_login, title="Iniciar sesión", icon="🔒")])
    else:
        pagina = st.navigation(
            [st.Page(pantalla_crear_administrador, title="Crear administrador", icon="🔑")]
        )
else:
    with st.sidebar:
        st.write(f"👤 Sesión: **{st.session_state['usuario']}**")
        if st.button("Cerrar sesión"):
            del st.session_state["usuario"]
            st.rerun()

    pagina = st.navigation([
        st.Page("paginas/inicio.py", title="Inicio", icon="🏥", default=True),
        st.Page("paginas/pacientes.py", title="Pacientes", icon="🧑"),
        st.Page("paginas/doctores.py", title="Doctores", icon="🩺"),
        st.Page("paginas/citas.py", title="Citas", icon="📅"),
        st.Page("paginas/calendario.py", title="Calendario", icon="🗓️"),
        st.Page("paginas/cuenta.py", title="Mi cuenta", icon="🔑"),
    ])

pagina.run()
