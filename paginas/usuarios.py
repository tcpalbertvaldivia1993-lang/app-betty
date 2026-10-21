"""Gestión de usuarios del personal (solo administradores)."""

import streamlit as st

import database as bd

st.title("👥 Usuarios")

# Defensa extra: app.py ya oculta esta página al personal
yo = bd.obtener_usuario(st.session_state["usuario"])
if yo["rol"] != "administrador":
    st.error("Solo el administrador puede gestionar usuarios.")
    st.stop()

pestana_nuevo, pestana_gestionar = st.tabs(["Nuevo usuario", "Gestionar usuarios"])

with pestana_nuevo:
    with st.form("form_nuevo_usuario", clear_on_submit=True):
        usuario = st.text_input("Usuario")
        rol = st.selectbox(
            "Rol", bd.ROLES, index=bd.ROLES.index("personal"),
            help="El personal usa toda la app excepto esta página. El administrador puede gestionar usuarios.",
        )
        contrasena = st.text_input(
            "Contraseña inicial", type="password",
            help=f"Mínimo {bd.LARGO_MINIMO_CONTRASENA} caracteres. "
                 "La persona puede cambiarla después en «Mi cuenta».",
        )
        repetir = st.text_input("Repite la contraseña", type="password")
        if st.form_submit_button("Crear usuario", type="primary"):
            if contrasena != repetir:
                st.error("Las contraseñas no coinciden.")
            else:
                try:
                    bd.crear_usuario(usuario, contrasena, rol)
                    st.success(f"Usuario «{usuario.strip()}» creado como {rol}.")
                except ValueError as error:
                    st.error(str(error))

with pestana_gestionar:
    usuarios = bd.listar_usuarios()
    tabla = usuarios.copy()
    tabla["activo"] = tabla["activo"].map({1: "Sí", 0: "No"})
    st.dataframe(tabla, hide_index=True, width="stretch")

    # No te puedes desactivar ni restablecer a ti mismo aquí (para tu contraseña usa «Mi cuenta»)
    otros = usuarios[usuarios["id"] != yo["id"]]
    if otros.empty:
        st.info("Todavía no hay otros usuarios.")
    else:
        opciones = {
            f"{fila.usuario} ({fila.rol}, {'activo' if fila.activo else 'inactivo'})": fila
            for fila in otros.itertuples()
        }
        elegido = opciones[st.selectbox("Selecciona un usuario", list(opciones))]

        col_activo, col_contrasena = st.columns(2)

        with col_activo:
            st.subheader("Acceso")
            if elegido.activo:
                st.caption("Un usuario desactivado no puede iniciar sesión, y si la tiene abierta se le cierra.")
                if st.button("Desactivar usuario"):
                    try:
                        bd.cambiar_activo_usuario(int(elegido.id), False)
                        st.rerun()
                    except ValueError as error:
                        st.error(str(error))
            else:
                if st.button("Reactivar usuario"):
                    bd.cambiar_activo_usuario(int(elegido.id), True)
                    st.rerun()

        with col_contrasena:
            st.subheader("Restablecer contraseña")
            st.caption("Para cuando alguien del personal olvida su contraseña.")
            with st.form("form_restablecer", clear_on_submit=True):
                nueva = st.text_input("Contraseña nueva", type="password")
                repetir_nueva = st.text_input("Repite la contraseña nueva", type="password")
                if st.form_submit_button("Restablecer"):
                    if nueva != repetir_nueva:
                        st.error("Las contraseñas no coinciden.")
                    else:
                        try:
                            bd.restablecer_contrasena(int(elegido.id), nueva)
                            st.success(f"Contraseña de «{elegido.usuario}» restablecida.")
                        except ValueError as error:
                            st.error(str(error))
