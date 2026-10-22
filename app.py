"""Entrada de la app de citas de la clínica.

Ejecutar con:  .venv/bin/streamlit run app.py

Antes de mostrar cualquier página pide usuario y contraseña.
La primera vez que se abre, pide crear la cuenta del administrador (el propietario).
El idioma (español o inglés) se elige en la barra lateral.
Con MODO_DEMO=1 funciona como demostración pública: cada visita tiene su propia base (ver demo.py).
"""

import streamlit as st

import database as bd
import demo
from traducciones import IDIOMAS, t, t_error

st.set_page_config(page_title=t("titulo_pestana"), page_icon="🏥", layout="wide")
if demo.ACTIVO:
    demo.preparar_visita()
else:
    bd.crear_tablas()

# Selector de idioma: se muestra siempre, también antes de iniciar sesión.
# Con key="idioma" la elección queda guardada en st.session_state["idioma"].
st.sidebar.selectbox("🌐 Idioma / Language", list(IDIOMAS), format_func=IDIOMAS.get, key="idioma")
if demo.ACTIVO:
    st.sidebar.warning(t("demo_aviso", horas=demo.HORAS_SIN_USO))


def pantalla_crear_administrador():
    """Se muestra solo la primera vez, cuando todavía no hay ningún usuario."""
    st.title(t("bienvenida_titulo"))
    st.write(t("bienvenida_texto"))
    with st.form("form_crear_administrador"):
        usuario = st.text_input(t("campo_usuario"))
        contrasena = st.text_input(
            t("campo_contrasena"), type="password",
            help=t("ayuda_contrasena", minimo=bd.LARGO_MINIMO_CONTRASENA),
        )
        repetir = st.text_input(t("campo_repetir_contrasena"), type="password")
        if st.form_submit_button(t("boton_crear_admin"), type="primary"):
            if contrasena != repetir:
                st.error(t("error_no_coinciden"))
            else:
                try:
                    bd.crear_usuario(usuario, contrasena, rol="administrador")
                    st.session_state["usuario"] = usuario.strip()
                    st.rerun()
                except ValueError as error:
                    st.error(t_error(error))


def pantalla_login():
    st.title(t("login_titulo"))
    with st.form("form_login"):
        usuario = st.text_input(t("campo_usuario"))
        contrasena = st.text_input(t("campo_contrasena"), type="password")
        if st.form_submit_button(t("boton_entrar"), type="primary"):
            if bd.verificar_usuario(usuario, contrasena):
                st.session_state["usuario"] = usuario.strip()
                st.rerun()
            else:
                # No se dice cuál de los dos falló, para no dar pistas
                st.error(t("error_login"))


if "usuario" in st.session_state:
    # Se vuelve a leer en cada recarga: si el administrador desactivó la cuenta, se cierra la sesión
    datos_usuario = bd.obtener_usuario(st.session_state["usuario"])
    if datos_usuario is None or not datos_usuario["activo"]:
        del st.session_state["usuario"]

if "usuario" not in st.session_state:
    # Sin sesión: la única página disponible es la de acceso
    if bd.hay_usuarios():
        pagina = st.navigation([st.Page(pantalla_login, title=t("pag_login"), icon="🔒")])
    else:
        pagina = st.navigation(
            [st.Page(pantalla_crear_administrador, title=t("pag_crear_admin"), icon="🔑")]
        )
else:
    with st.sidebar:
        st.write(t("sesion", usuario=datos_usuario["usuario"], rol=t(f"rol_{datos_usuario['rol']}")))
        if st.button(t("boton_cerrar_sesion")):
            del st.session_state["usuario"]
            st.rerun()

    paginas = [
        st.Page("paginas/inicio.py", title=t("pag_inicio"), icon="🏥", default=True),
        st.Page("paginas/pacientes.py", title=t("pag_pacientes"), icon="🧑"),
        st.Page("paginas/doctores.py", title=t("pag_doctores"), icon="🩺"),
        st.Page("paginas/citas.py", title=t("pag_citas"), icon="📅"),
        st.Page("paginas/calendario.py", title=t("pag_calendario"), icon="🗓️"),
        st.Page("paginas/cuenta.py", title=t("pag_cuenta"), icon="🔑"),
    ]
    # Solo el administrador puede gestionar los usuarios del personal
    if datos_usuario["rol"] == "administrador":
        paginas.append(st.Page("paginas/usuarios.py", title=t("pag_usuarios"), icon="👥"))
        paginas.append(st.Page("paginas/reiniciar.py", title=t("pag_reiniciar"), icon="⚠️"))
    pagina = st.navigation(paginas)

pagina.run()
