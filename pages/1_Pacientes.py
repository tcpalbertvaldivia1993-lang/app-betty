"""Registrar, buscar y editar pacientes."""

from datetime import date

import streamlit as st

import database as bd

st.set_page_config(page_title="Pacientes", page_icon="🧑", layout="wide")
bd.crear_tablas()
st.title("🧑 Pacientes")

pestana_nuevo, pestana_buscar = st.tabs(["Nuevo paciente", "Buscar y editar"])

with pestana_nuevo:
    with st.form("form_nuevo_paciente", clear_on_submit=True):
        col1, col2 = st.columns(2)
        nombre = col1.text_input("Nombre *")
        apellido = col2.text_input("Apellido *")
        telefono = col1.text_input("Teléfono")
        email = col2.text_input("Email")
        fecha_nacimiento = col1.date_input(
            "Fecha de nacimiento", value=None, min_value=date(1900, 1, 1), max_value=date.today()
        )
        notas = st.text_area("Notas")
        if st.form_submit_button("Guardar paciente", type="primary"):
            try:
                bd.agregar_paciente(nombre, apellido, telefono, email, fecha_nacimiento, notas)
                st.success(f"Paciente {nombre} {apellido} guardado.")
            except ValueError as error:
                st.error(str(error))

with pestana_buscar:
    texto = st.text_input("Buscar por nombre, apellido o teléfono")
    pacientes = bd.buscar_pacientes(texto) if texto else bd.listar_pacientes()

    if pacientes.empty:
        st.info("No se encontraron pacientes.")
    else:
        st.dataframe(
            pacientes[["id", "nombre", "apellido", "telefono", "email", "fecha_nacimiento"]],
            hide_index=True,
            width="stretch",
        )

        st.subheader("Editar paciente")
        opciones = {
            f"{fila.nombre} {fila.apellido} (#{fila.id})": fila
            for fila in pacientes.itertuples()
        }
        elegido = opciones[st.selectbox("Paciente", list(opciones))]

        with st.form("form_editar_paciente"):
            col1, col2 = st.columns(2)
            nombre = col1.text_input("Nombre *", value=elegido.nombre)
            apellido = col2.text_input("Apellido *", value=elegido.apellido)
            telefono = col1.text_input("Teléfono", value=elegido.telefono or "")
            email = col2.text_input("Email", value=elegido.email or "")
            nacimiento_actual = (
                date.fromisoformat(elegido.fecha_nacimiento) if elegido.fecha_nacimiento else None
            )
            fecha_nacimiento = col1.date_input(
                "Fecha de nacimiento", value=nacimiento_actual,
                min_value=date(1900, 1, 1), max_value=date.today(),
            )
            notas = st.text_area("Notas", value=elegido.notas or "")
            if st.form_submit_button("Guardar cambios", type="primary"):
                try:
                    bd.actualizar_paciente(
                        int(elegido.id), nombre, apellido, telefono, email, fecha_nacimiento, notas
                    )
                    st.success("Cambios guardados.")
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))
