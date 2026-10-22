"""Descargar una copia de seguridad de los datos de la clínica (solo administradores).

Pensada para la clínica, sin conocimientos técnicos: un botón prepara la copia y otros
dos la descargan como cualquier archivo, para guardarla en un USB o en su nube.
- Archivo de la app (.db): todos los datos, con los usuarios. Sirve para restaurar
  (restaurar_nube.py) o para abrirlo con la app en una computadora.
- Excel (.xlsx): pacientes, doctores y citas, para leerlos en Excel.
"""

import io
import tempfile
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

import database as bd
from traducciones import formatear_fecha, preparar_tabla, t

st.title(t("copia_titulo"))

# Defensa extra: app.py ya oculta esta página al personal
yo = bd.obtener_usuario(st.session_state["usuario"])
if yo["rol"] != "administrador":
    st.error(t("solo_admin"))
    st.stop()

st.write(t("copia_explicacion"))

dias = bd.dias_desde_ultima_copia()
if dias is None:
    st.warning(t("copia_nunca"))
elif dias >= bd.DIAS_ENTRE_COPIAS:
    st.warning(t("copia_vieja", fecha=formatear_fecha(bd.ultima_copia()), dias=dias))
else:
    st.success(t("copia_reciente", fecha=formatear_fecha(bd.ultima_copia())))

st.info(t("copia_cuidado"))


def preparar_archivo_app():
    """Los datos de la clínica en un archivo SQLite con el formato de la app (bytes)."""
    esquema = bd.esquema_sesion.get()
    clinica = bd.usar_clinica(esquema) if esquema else None
    info = {
        "esquema": esquema or "",
        "nombre": clinica["nombre"] if clinica else "",
        "temporal": "1" if clinica and clinica["temporal"] else "0",
    }
    with tempfile.TemporaryDirectory() as carpeta:
        archivo = Path(carpeta) / "copia.db"
        bd.exportar_sqlite(archivo, info)
        return archivo.read_bytes()


def preparar_excel():
    """Pacientes, doctores y citas en un Excel, una hoja por cada uno (bytes)."""
    citas = bd.citas_por_rango("0001-01-01", "9999-12-31")  # todas
    hojas = {
        t("pag_pacientes"): bd.listar_pacientes().drop(columns=["notas"], errors="ignore"),
        t("pag_doctores"): bd.listar_doctores(solo_activos=False),
        t("pag_citas"): citas[["fecha", "hora_inicio", "duracion_min", "paciente", "doctor",
                               "especialidad", "motivo", "estado"]],
    }
    salida = io.BytesIO()
    with pd.ExcelWriter(salida, engine="openpyxl") as excel:
        for nombre, tabla in hojas.items():
            preparar_tabla(tabla).to_excel(excel, sheet_name=nombre, index=False)
    return salida.getvalue()


if st.button(t("boton_preparar_copia"), type="primary"):
    with st.spinner(t("preparando_copia")):
        st.session_state["copia_archivos"] = {
            "app": preparar_archivo_app(),
            "excel": preparar_excel(),
            "fecha": date.today().isoformat(),
        }

archivos = st.session_state.get("copia_archivos")
if archivos:
    st.write(t("copia_lista"))
    col_app, col_excel = st.columns(2)
    # Al pulsar una descarga, la página se recarga y el botón devuelve True: se anota la copia
    if col_app.download_button(
        t("boton_descargar_app"), data=archivos["app"],
        file_name=f"copia_clinica_{archivos['fecha']}.db",
        mime="application/vnd.sqlite3", help=t("ayuda_descargar_app"),
    ):
        bd.registrar_copia()
    if col_excel.download_button(
        t("boton_descargar_excel"), data=archivos["excel"],
        file_name=f"copia_clinica_{archivos['fecha']}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        help=t("ayuda_descargar_excel"),
    ):
        bd.registrar_copia()
