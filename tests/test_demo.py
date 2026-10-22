"""Pruebas del modo demostración (demo.py): cada visita tiene su propia base de datos."""

import os
import sys
import time
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ))
import database as bd  # noqa: E402
import demo  # noqa: E402


@pytest.fixture
def modo_demo(tmp_path, monkeypatch):
    """Activa la demostración con las bases de las visitas en una carpeta temporal."""
    monkeypatch.setattr(demo, "ACTIVO", True)
    monkeypatch.setattr(demo, "CARPETA", tmp_path / "visitas")
    # Si algo usara la base normal en vez de la de la visita, iría a parar aquí
    monkeypatch.setattr(bd, "RUTA_BD", tmp_path / "no_usar.db")
    yield tmp_path
    bd.ruta_sesion.set(None)  # AppTest corre en este mismo hilo: que no afecte a otras pruebas


def _abrir(codigo=None):
    app = AppTest.from_file(str(RAIZ / "app.py"), default_timeout=30)
    if codigo:
        app.query_params["demo"] = codigo
    app.run()
    assert not app.exception
    return app


def _crear_administrador(app, usuario="dueno", contrasena="secreta123"):
    app.text_input[0].input(usuario)
    app.text_input[1].input(contrasena)
    app.text_input[2].input(contrasena)
    app.button[0].click()
    app.run()
    assert not app.exception


def _carpetas(modo_demo):
    return sorted((modo_demo / "visitas").iterdir())


def test_visita_nueva_pide_crear_administrador_y_tiene_datos(modo_demo):
    app = _abrir()
    assert len(app.text_input) == 3  # usuario, contraseña y repetir: pantalla "Bienvenido"
    [carpeta] = _carpetas(modo_demo)
    assert app.query_params["demo"] == carpeta.name
    bd.ruta_sesion.set(carpeta / "clinica.db")
    assert not bd.listar_pacientes().empty
    assert not bd.hay_usuarios()
    assert not (modo_demo / "no_usar.db").exists()


def test_cada_visita_tiene_sus_propios_datos(modo_demo):
    primera = _abrir()
    _crear_administrador(primera)
    assert primera.title[0].value != _abrir().title[0].value  # la segunda visita sigue en "Bienvenido"
    assert len(_carpetas(modo_demo)) == 2


def test_volver_con_el_codigo_conserva_los_datos(modo_demo):
    primera = _abrir()
    _crear_administrador(primera)
    codigo = primera.query_params["demo"]

    # Como recargar con F5: sesión nueva, misma dirección
    otra_vez = _abrir(codigo)
    assert len(otra_vez.text_input) == 2  # pide iniciar sesión, no crear administrador
    assert len(_carpetas(modo_demo)) == 1


def test_cambiar_de_pagina_sigue_en_la_misma_visita(modo_demo):
    app = _abrir()
    _crear_administrador(app)
    codigo = app.query_params["demo"]
    for pagina in ("paginas/pacientes.py", "paginas/usuarios.py", "paginas/cuenta.py"):
        app.switch_page(str(RAIZ / pagina))
        app.run()
        assert not app.exception
        assert app.query_params["demo"] == codigo
    assert len(_carpetas(modo_demo)) == 1


@pytest.mark.parametrize("codigo", ["../../etc", "abc", "0" * 32])
def test_codigo_falso_o_borrado_crea_visita_nueva(modo_demo, codigo):
    app = _abrir(codigo)
    assert app.query_params["demo"] != codigo
    assert len(_carpetas(modo_demo)) == 1


def test_se_borran_las_visitas_viejas(modo_demo):
    vieja = demo.CARPETA / ("a" * 32)
    reciente = demo.CARPETA / ("b" * 32)
    vieja.mkdir(parents=True)
    reciente.mkdir()
    hace_dos_dias = time.time() - 48 * 3600
    os.utime(vieja, (hace_dos_dias, hace_dos_dias))

    demo.borrar_visitas_viejas()
    assert not vieja.exists()
    assert reciente.exists()


def test_sin_demo_no_cambia_nada(tmp_path, monkeypatch):
    monkeypatch.setattr(bd, "RUTA_BD", tmp_path / "clinica.db")
    app = AppTest.from_file(str(RAIZ / "app.py"), default_timeout=30)
    app.run()
    assert not app.exception
    assert not app.sidebar.warning  # sin aviso de demostración
    assert "demo" not in app.query_params
    assert (tmp_path / "clinica.db").exists()
    assert bd.listar_pacientes().empty  # sin datos de ejemplo
