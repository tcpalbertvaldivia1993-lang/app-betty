"""Modo demostración, para publicar la app en internet (por ejemplo en Streamlit Community Cloud).

Se activa con la variable de entorno MODO_DEMO=1. En Streamlit Community Cloud se pone en
"Advanced settings → Secrets" como:  MODO_DEMO = "1"

En modo demostración cada visita tiene su propia base de datos, privada y temporal:
- La primera vez sale la pantalla "Bienvenido" para crear su propio administrador, igual que
  al instalar la app en una clínica, y ya hay datos de ejemplo para probar.
- Nadie ve los datos de las demás visitas.
- La dirección lleva un código (?demo=...), así que al recargar la página no se pierde nada.
- Las bases que llevan más de 24 horas sin usarse se borran solas.

Sin MODO_DEMO, la app funciona como siempre (instalación en la clínica).
"""

import os
import re
import shutil
import tempfile
import time
import uuid
from pathlib import Path

import streamlit as st

import database as bd
import datos_ejemplo

ACTIVO = os.environ.get("MODO_DEMO") == "1"
CARPETA = Path(tempfile.gettempdir()) / "clinica-demo"
HORAS_SIN_USO = 24

# El código de cada visita: 32 letras y números (así nadie puede usarlo para salir de CARPETA)
FORMATO_CODIGO = re.compile(r"[0-9a-f]{32}")


def borrar_visitas_viejas():
    """Borra las bases de las visitas que llevan más de HORAS_SIN_USO sin usarse."""
    limite = time.time() - HORAS_SIN_USO * 3600
    if not CARPETA.exists():
        return
    for carpeta in CARPETA.iterdir():
        if carpeta.is_dir() and carpeta.stat().st_mtime < limite:
            shutil.rmtree(carpeta, ignore_errors=True)


def preparar_visita():
    """Elige la base de datos de esta visita (y la crea con datos de ejemplo si es nueva).

    Se llama al principio de cada recarga de app.py.
    """
    # El código se guarda en la sesión y en la dirección: al cambiar de página el menú
    # borra la dirección, y al recargar con F5 se pierde la sesión
    codigo = st.session_state.get("demo_codigo") or st.query_params.get("demo", "")
    carpeta = CARPETA / codigo
    if not FORMATO_CODIGO.fullmatch(codigo) or not carpeta.is_dir():
        # Visita nueva (o código que ya se borró): base nueva con datos de ejemplo
        borrar_visitas_viejas()
        codigo = uuid.uuid4().hex
        carpeta = CARPETA / codigo
        carpeta.mkdir(parents=True)
        bd.ruta_sesion.set(carpeta / "clinica.db")
        datos_ejemplo.cargar()
    else:
        bd.ruta_sesion.set(carpeta / "clinica.db")
        os.utime(carpeta)  # marca que se usó, para que no se borre
    bd.crear_tablas()

    st.session_state["demo_codigo"] = codigo
    if st.query_params.get("demo") != codigo:
        st.query_params["demo"] = codigo
