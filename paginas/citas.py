"""Agendar, reprogramar y cambiar el estado de las citas."""

from datetime import date, timedelta

import streamlit as st

import database as bd

st.title("📅 Citas")

# Horarios disponibles: cada 30 minutos de 08:00 a 17:30
HORAS = [f"{h:02d}:{m:02d}" for h in range(8, 18) for m in (0, 30)]

pacientes = bd.listar_pacientes()
doctores = bd.listar_doctores()

pestana_nueva, pestana_gestionar = st.tabs(["Agendar cita", "Gestionar citas"])

with pestana_nueva:
    if pacientes.empty or doctores.empty:
        st.warning("Primero registra al menos un paciente y un doctor activo.")
    else:
        opciones_pacientes = {
            f"{fila.nombre} {fila.apellido} - {fila.telefono or 'sin tel.'}": int(fila.id)
            for fila in pacientes.itertuples()
        }
        opciones_doctores = {
            f"{fila.nombre} ({fila.especialidad})": int(fila.id)
            for fila in doctores.itertuples()
        }

        with st.form("form_nueva_cita"):
            col1, col2 = st.columns(2)
            paciente = col1.selectbox("Paciente", list(opciones_pacientes))
            doctor = col2.selectbox("Doctor", list(opciones_doctores))
            fecha = col1.date_input("Fecha", min_value=date.today(), format="DD/MM/YYYY")
            hora = col2.selectbox("Hora", HORAS)
            duracion = col1.selectbox("Duración (minutos)", [15, 30, 45, 60], index=1)
            motivo = col2.text_input("Motivo de la consulta")
            if st.form_submit_button("Agendar", type="primary"):
                try:
                    bd.agendar_cita(
                        opciones_pacientes[paciente], opciones_doctores[doctor],
                        fecha, hora, duracion, motivo,
                    )
                    st.success(f"Cita agendada: {paciente} con {doctor}, {fecha:%d/%m/%Y} a las {hora}.")
                except ValueError as error:
                    st.error(str(error))

with pestana_gestionar:
    col1, col2 = st.columns(2)
    desde = col1.date_input("Desde", value=date.today(), format="DD/MM/YYYY")
    hasta = col2.date_input("Hasta", value=date.today() + timedelta(days=30), format="DD/MM/YYYY")
    citas = bd.citas_por_rango(desde, hasta)

    if citas.empty:
        st.info("No hay citas en ese rango.")
    else:
        st.dataframe(
            citas[["id", "fecha", "hora_inicio", "duracion_min", "paciente", "doctor", "motivo", "estado"]],
            hide_index=True,
            width="stretch",
        )

        opciones_citas = {
            f"#{fila.id} · {fila.fecha} {fila.hora_inicio} · {fila.paciente} con {fila.doctor} [{fila.estado}]": fila
            for fila in citas.itertuples()
        }
        cita = opciones_citas[st.selectbox("Selecciona una cita", list(opciones_citas))]

        col_estado, col_reprogramar = st.columns(2)

        with col_estado:
            st.subheader("Cambiar estado")
            nuevo_estado = st.radio(
                "Estado", bd.ESTADOS_CITA, index=bd.ESTADOS_CITA.index(cita.estado), horizontal=True
            )
            if st.button("Actualizar estado"):
                bd.cambiar_estado_cita(int(cita.id), nuevo_estado)
                st.rerun()

        with col_reprogramar:
            st.subheader("Reprogramar")
            fecha_actual = date.fromisoformat(cita.fecha)
            nueva_fecha = st.date_input(
                "Nueva fecha", value=max(fecha_actual, date.today()),
                min_value=date.today(), format="DD/MM/YYYY",
            )
            indice_hora = HORAS.index(cita.hora_inicio) if cita.hora_inicio in HORAS else 0
            nueva_hora = st.selectbox("Nueva hora", HORAS, index=indice_hora)
            if st.button("Reprogramar"):
                try:
                    bd.reprogramar_cita(int(cita.id), nueva_fecha, nueva_hora)
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))
