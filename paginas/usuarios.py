"""Gestión de usuarios del personal (solo administradores)."""

import streamlit as st

import database as bd
from traducciones import formato_opcion, preparar_tabla, t, t_error

st.title(t("usuarios_titulo"))

# Defensa extra: app.py ya oculta esta página al personal
yo = bd.obtener_usuario(st.session_state["usuario"])
if yo["rol"] != "administrador":
    st.error(t("solo_admin"))
    st.stop()

pestana_nuevo, pestana_gestionar = st.tabs([t("tab_nuevo_usuario"), t("tab_gestionar_usuarios")])

with pestana_nuevo:
    with st.form("form_nuevo_usuario", clear_on_submit=True):
        usuario = st.text_input(t("campo_usuario"))
        rol = st.selectbox(
            t("campo_rol"), bd.ROLES, index=bd.ROLES.index("personal"),
            format_func=formato_opcion("rol_"), help=t("ayuda_rol"),
        )
        contrasena = st.text_input(
            t("campo_contrasena_inicial"), type="password",
            help=t("ayuda_contrasena_inicial", minimo=bd.LARGO_MINIMO_CONTRASENA),
        )
        repetir = st.text_input(t("campo_repetir_contrasena"), type="password")
        if st.form_submit_button(t("boton_crear_usuario"), type="primary"):
            if contrasena != repetir:
                st.error(t("error_no_coinciden"))
            else:
                try:
                    bd.crear_usuario(usuario, contrasena, rol)
                    st.success(t("usuario_creado", usuario=usuario.strip(), rol=t(f"rol_{rol}")))
                except ValueError as error:
                    st.error(t_error(error))

with pestana_gestionar:
    usuarios = bd.listar_usuarios()
    st.dataframe(preparar_tabla(usuarios), hide_index=True, width="stretch")

    # No te puedes desactivar ni restablecer a ti mismo aquí (para tu contraseña usa «Mi cuenta»)
    otros = usuarios[usuarios["id"] != yo["id"]]
    if otros.empty:
        st.info(t("sin_otros_usuarios"))
    else:
        opciones = {
            t(
                "opcion_usuario", usuario=fila.usuario, rol=t(f"rol_{fila.rol}"),
                estado=t("usuario_activo") if fila.activo else t("usuario_inactivo"),
            ): fila
            for fila in otros.itertuples()
        }
        elegido = opciones[st.selectbox(t("selecciona_usuario"), list(opciones))]

        col_activo, col_contrasena = st.columns(2)

        with col_activo:
            st.subheader(t("acceso"))
            if elegido.activo:
                st.caption(t("desactivar_usuario_ayuda"))
                if st.button(t("boton_desactivar_usuario")):
                    try:
                        bd.cambiar_activo_usuario(int(elegido.id), False)
                        st.rerun()
                    except ValueError as error:
                        st.error(t_error(error))
            else:
                if st.button(t("boton_reactivar_usuario")):
                    bd.cambiar_activo_usuario(int(elegido.id), True)
                    st.rerun()

        with col_contrasena:
            st.subheader(t("restablecer_titulo"))
            st.caption(t("restablecer_ayuda"))
            with st.form("form_restablecer", clear_on_submit=True):
                nueva = st.text_input(t("campo_contrasena_nueva"), type="password")
                repetir_nueva = st.text_input(t("campo_repetir_nueva"), type="password")
                if st.form_submit_button(t("boton_restablecer")):
                    if nueva != repetir_nueva:
                        st.error(t("error_no_coinciden"))
                    else:
                        try:
                            bd.restablecer_contrasena(int(elegido.id), nueva)
                            st.success(t("contrasena_restablecida", usuario=elegido.usuario))
                        except ValueError as error:
                            st.error(t_error(error))
