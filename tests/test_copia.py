"""Pruebas de la página Copia de seguridad (paginas/copia.py), con SQLite."""

import io
import sys
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ))
import database as bd  # noqa: E402
import datos_ejemplo  # noqa: E402
import nube  # noqa: E402


@pytest.fixture
def app_con_datos(tmp_path, monkeypatch):
    """La app en SQLite, con datos de ejemplo y un administrador con la sesión iniciada."""
    monkeypatch.setattr(bd, "URL_POSTGRES", None)
    monkeypatch.setattr(nube, "ACTIVO", False)
    monkeypatch.setattr(bd, "RUTA_BD", tmp_path / "clinica.db")
    datos_ejemplo.cargar()
    bd.crear_usuario("dueno", "secreta123", rol="administrador")
    bd.crear_usuario("recepcion", "secreta123")
    return tmp_path


def _entrar(usuario):
    app = AppTest.from_file(str(RAIZ / "app.py"), default_timeout=60)
    app.run()
    app.text_input[0].input(usuario)
    app.text_input[1].input("secreta123")
    app.button[0].click()
    app.run()
    assert not app.exception
    return app


def _recordatorio(app):
    return any("copia de seguridad" in w.value for w in app.sidebar.warning)


def test_preparar_y_descargar_copia(app_con_datos):
    app = _entrar("dueno")
    assert _recordatorio(app)  # nunca se descargó una copia
    app.switch_page(str(RAIZ / "paginas/copia.py"))
    app.run()
    assert not app.exception
    assert any("ninguna copia" in w.value for w in app.warning)

    [b for b in app.button if b.label == "Preparar la copia"][0].click()
    app.run()
    assert not app.exception
    archivos = app.session_state["copia_archivos"]

    # El archivo de la app tiene todos los datos
    copia = app_con_datos / "descargada.db"
    copia.write_bytes(archivos["app"])
    assert bd.contar_datos(copia) == {"citas": 212, "doctores": 4, "pacientes": 12}
    assert bd.verificar_usuario("recepcion", "secreta123", copia)

    # El Excel tiene una hoja por cada cosa, con los nombres de columna traducidos
    hojas = pd.read_excel(io.BytesIO(archivos["excel"]), sheet_name=None)
    assert list(hojas) == ["Pacientes", "Doctores", "Citas"]
    assert [len(hojas[h]) for h in hojas] == [12, 4, 212]
    assert {"Paciente", "Doctor", "Estado"} <= set(hojas["Citas"].columns)
    assert set(hojas["Citas"]["Estado"]) <= {"programada", "atendida", "cancelada", "no asistió"}


def test_el_recordatorio_desaparece_despues_de_la_copia(app_con_datos):
    bd.registrar_copia()
    app = _entrar("dueno")
    assert not _recordatorio(app)
    app.switch_page(str(RAIZ / "paginas/copia.py"))
    app.run()
    assert any("Última copia" in s.value for s in app.success)


def test_el_personal_no_ve_la_copia(app_con_datos):
    app = _entrar("recepcion")
    assert not _recordatorio(app)
    with pytest.raises(ValueError):
        app.switch_page(str(RAIZ / "paginas/copia.py"))
