"""Agendar, reprogramar y cambiar el estado de las citas."""

from datetime import date, timedelta

import streamlit as st

import database as bd
from traducciones import formatear_fecha, formato_opcion, preparar_tabla, t, t_error

st.title(t("citas_titulo"))

# Horarios disponibles: cada 30 minutos de 08:00 a 17:30
HORAS = [f"{h:02d}:{m:02d}" for h in range(8, 18) for m in (0, 30)]

pacientes = bd.listar_pacientes()
doctores = bd.listar_doctores()

pestana_nueva, pestana_gestionar = st.tabs([t("tab_agendar"), t("tab_gestionar_citas")])

with pestana_nueva:
    if pacientes.empty or doctores.empty:
        st.warning(t("aviso_falta_paciente_doctor"))
    else:
        opciones_pacientes = {
            f"{fila.nombre} {fila.apellido} - {fila.telefono or t('sin_telefono')}": int(fila.id)
            for fila in pacientes.itertuples()
        }
        opciones_doctores = {
            f"{fila.nombre} ({fila.especialidad})": int(fila.id)
            for fila in doctores.itertuples()
        }

        with st.form("form_nueva_cita"):
            col1, col2 = st.columns(2)
            paciente = col1.selectbox(t("campo_paciente"), list(opciones_pacientes))
            doctor = col2.selectbox(t("campo_doctor"), list(opciones_doctores))
            fecha = col1.date_input(t("campo_fecha"), min_value=date.today(), format=t("formato_fecha"))
            hora = col2.selectbox(t("campo_hora"), HORAS)
            duracion = col1.selectbox(t("campo_duracion"), [15, 30, 45, 60], index=1)
            motivo = col2.text_input(t("campo_motivo"))
            if st.form_submit_button(t("boton_agendar"), type="primary"):
                try:
                    bd.agendar_cita(
                        opciones_pacientes[paciente], opciones_doctores[doctor],
                        fecha, hora, duracion, motivo,
                    )
                    st.success(t(
                        "cita_agendada", paciente=paciente, doctor=doctor,
                        fecha=formatear_fecha(fecha), hora=hora,
                    ))
                except ValueError as error:
                    st.error(t_error(error))

with pestana_gestionar:
    col1, col2 = st.columns(2)
    desde = col1.date_input(t("campo_desde"), value=date.today(), format=t("formato_fecha"))
    hasta = col2.date_input(
        t("campo_hasta"), value=date.today() + timedelta(days=30), format=t("formato_fecha")
    )
    citas = bd.citas_por_rango(desde, hasta)

    if citas.empty:
        st.info(t("sin_citas_rango"))
    else:
        st.dataframe(
            preparar_tabla(
                citas[["id", "fecha", "hora_inicio", "duracion_min", "paciente", "doctor", "motivo", "estado"]]
            ),
            hide_index=True,
            width="stretch",
        )

        opciones_citas = {
            t(
                "opcion_cita", id=fila.id, fecha=formatear_fecha(date.fromisoformat(fila.fecha)),
                hora=fila.hora_inicio, paciente=fila.paciente, doctor=fila.doctor,
                estado=t(f"estado_{fila.estado}"),
            ): fila
            for fila in citas.itertuples()
        }
        cita = opciones_citas[st.selectbox(t("selecciona_cita"), list(opciones_citas))]

        col_estado, col_reprogramar = st.columns(2)

        with col_estado:
            st.subheader(t("cambiar_estado"))
            nuevo_estado = st.radio(
                t("campo_estado"), bd.ESTADOS_CITA, index=bd.ESTADOS_CITA.index(cita.estado),
                format_func=formato_opcion("estado_"), horizontal=True,
            )
            if st.button(t("boton_actualizar_estado")):
                bd.cambiar_estado_cita(int(cita.id), nuevo_estado)
                st.rerun()

        with col_reprogramar:
            st.subheader(t("reprogramar"))
            fecha_actual = date.fromisoformat(cita.fecha)
            nueva_fecha = st.date_input(
                t("campo_nueva_fecha"), value=max(fecha_actual, date.today()),
                min_value=date.today(), format=t("formato_fecha"),
            )
            indice_hora = HORAS.index(cita.hora_inicio) if cita.hora_inicio in HORAS else 0
            nueva_hora = st.selectbox(t("campo_nueva_hora"), HORAS, index=indice_hora)
            if st.button(t("reprogramar")):
                try:
                    bd.reprogramar_cita(int(cita.id), nueva_fecha, nueva_hora)
                    st.rerun()
                except ValueError as error:
                    st.error(t_error(error))
