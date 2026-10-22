"""Modo nube: la app publicada en internet, con varias clínicas guardadas en PostgreSQL (Neon).

Se activa cuando existe la variable DATABASE_URL. En Streamlit Community Cloud se pone en
"Settings → Secrets", junto con el código de invitación:

    DATABASE_URL = "postgresql://..."
    CODIGO_INVITACION = "el-codigo-que-das-a-cada-clinica"

Sin sesión iniciada hay tres pestañas:
- Iniciar sesión: cada usuario entra en su clínica (el administrador y su personal).
- Crear clínica: pide el código de invitación. Sus datos se guardan para siempre.
- Probar la demostración: una clínica temporal con datos de ejemplo, sin código.
  Se borra sola tras bd.HORAS_DEMO horas sin uso.

Sin DATABASE_URL, la app funciona como siempre con SQLite (programa para Windows).
"""

import hmac
import os

import streamlit as st

import database as bd
import datos_ejemplo
from traducciones import t, t_error



def _secreto(nombre):
    """Lee un valor de las variables de entorno o, si no está, de los Secrets de Streamlit.

    Streamlit Community Cloud copia los Secrets a variables de entorno solo al arrancar el
    servidor; st.secrets siempre tiene los valores guardados.
    """
    if os.environ.get(nombre):
        return os.environ[nombre]
    try:
        return st.secrets.get(nombre)
    except Exception:  # no hay archivo de Secrets (p. ej. en la computadora o en el .exe)
        return None


def problema_con_los_secrets():
    """Si hay Secrets pero la app no encuentra DATABASE_URL, explica por qué. Si no, None.

    Nunca muestra los valores (llevan contraseñas): solo los nombres o el tipo de error.
    Sin archivo de Secrets (en la computadora o en el .exe) no hay nada que avisar.
    """
    try:
        nombres = list(st.secrets.keys())
    except Exception as error:
        if getattr(error, "error_id", "") == "no-secrets-found" or isinstance(error, FileNotFoundError):
            return None
        return t("secrets_con_error", tipo=type(error).__name__)
    if "DATABASE_URL" in nombres:
        return None
    return t("secrets_sin_url", nombres=", ".join(nombres) or "-")


ACTIVO = bd.usa_postgres()
CODIGO_INVITACION = os.environ.get("CODIGO_INVITACION", "")


def configurar():
    """Lee DATABASE_URL y el código de invitación. app.py la llama en cada recarga.

    Se lee cada vez (y no solo al arrancar) porque en Streamlit Community Cloud los Secrets
    se pueden cambiar mientras la app está funcionando.
    """
    global ACTIVO, CODIGO_INVITACION
    url = _secreto("DATABASE_URL")
    if url:
        bd.URL_POSTGRES = url
    ACTIVO = bd.usa_postgres()
    CODIGO_INVITACION = _secreto("CODIGO_INVITACION") or CODIGO_INVITACION


@st.cache_resource
def preparar():
    """Crea las tablas comunes de la nube (una sola vez por servidor)."""
    bd.preparar_nube()


def codigo_valido(codigo):
    """True si el código de invitación es el correcto (sin dar pistas por el tiempo que tarda)."""
    if not CODIGO_INVITACION:
        return False
    return hmac.compare_digest(codigo.strip().encode("utf-8"), CODIGO_INVITACION.encode("utf-8"))


def abrir_clinica_de_la_sesion():
    """Elige la clínica de la sesión para esta recarga. Devuelve sus datos, o None si ya no existe."""
    bd.esquema_sesion.set(None)  # nada de la recarga anterior: solo la clínica de esta sesión
    esquema = st.session_state.get("esquema")
    if not esquema:
        return None
    clinica = bd.usar_clinica(esquema)
    if clinica is not None:
        bd.esquema_sesion.set(esquema)
    return clinica


def _entrar(usuario, esquema):
    st.session_state["usuario"] = usuario.strip()
    st.session_state["esquema"] = esquema
    st.rerun()


def _formulario_iniciar_sesion():
    with st.form("form_login"):
        usuario = st.text_input(t("campo_usuario"), key="login_usuario")
        contrasena = st.text_input(t("campo_contrasena"), type="password", key="login_contrasena")
        if st.form_submit_button(t("boton_entrar"), type="primary"):
            esquema = bd.esquema_de_usuario(usuario)
            if esquema is not None:
                bd.esquema_sesion.set(esquema)
            if esquema is not None and bd.verificar_usuario(usuario, contrasena):
                _entrar(usuario, esquema)
            else:
                # No se dice cuál de los dos falló, para no dar pistas
                st.error(t("error_login"))


def _formulario_crear_clinica(temporal):
    """Formulario para crear una clínica real (con código) o una de demostración."""
    formulario = "demo" if temporal else "clinica"  # para que los campos de los dos no se mezclen
    with st.form(f"form_{formulario}"):
        nombre = st.text_input(
            t("campo_nombre_clinica"), value=t("nombre_clinica_demo") if temporal else "",
            key=f"{formulario}_nombre",
        )
        codigo = "" if temporal else st.text_input(
            t("campo_codigo_invitacion"), type="password", help=t("ayuda_codigo_invitacion"),
            key=f"{formulario}_codigo",
        )
        usuario = st.text_input(t("campo_usuario"), key=f"{formulario}_usuario")
        contrasena = st.text_input(
            t("campo_contrasena"), type="password",
            help=t("ayuda_contrasena", minimo=bd.LARGO_MINIMO_CONTRASENA),
            key=f"{formulario}_contrasena",
        )
        repetir = st.text_input(
            t("campo_repetir_contrasena"), type="password", key=f"{formulario}_repetir"
        )
        # La demostración siempre trae datos de ejemplo; una clínica real empieza vacía si se quiere
        con_ejemplos = temporal or st.checkbox(t("casilla_datos_ejemplo"), key=f"{formulario}_ejemplos")
        boton = t("boton_probar_demo") if temporal else t("boton_crear_clinica")
        if not st.form_submit_button(boton, type="primary"):
            return

    if not temporal and not codigo_valido(codigo):
        st.error(t("error_codigo_invitacion"))
    elif contrasena != repetir:
        st.error(t("error_no_coinciden"))
    else:
        try:
            with st.spinner(t("creando_clinica")):
                if temporal:
                    bd.borrar_clinicas_temporales_viejas()  # aprovecha para limpiar las viejas
                esquema = bd.crear_clinica(nombre, usuario, contrasena, temporal=temporal)
                if con_ejemplos:
                    bd.esquema_sesion.set(esquema)
                    datos_ejemplo.cargar()
            _entrar(usuario, esquema)
        except ValueError as error:
            st.error(t_error(error))


def pantalla_acceso():
    """Pantalla sin sesión iniciada: entrar, crear una clínica o probar la demostración."""
    st.title(t("acceso_titulo"))
    entrar, crear, probar = st.tabs(
        [t("pestana_entrar"), t("pestana_crear_clinica"), t("pestana_demo")]
    )
    with entrar:
        _formulario_iniciar_sesion()
    with crear:
        if not CODIGO_INVITACION:
            st.info(t("registro_cerrado"))
        else:
            st.write(t("crear_clinica_explicacion"))
            _formulario_crear_clinica(temporal=False)
    with probar:
        st.write(t("demo_explicacion", horas=bd.HORAS_DEMO))
        _formulario_crear_clinica(temporal=True)
