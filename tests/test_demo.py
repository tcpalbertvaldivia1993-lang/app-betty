"""Pruebas del modo demostración (demo.py), con una base de datos temporal."""

import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ))
import database as bd  # noqa: E402
import demo  # noqa: E402


@pytest.fixture
def base_temporal(tmp_path, monkeypatch):
    """Hace que toda la app use una base de datos temporal y vacía."""
    monkeypatch.setattr(bd, "RUTA_BD", tmp_path / "demo.db")
    bd.crear_tablas()


def test_preparar_crea_usuario_y_datos(base_temporal):
    demo.preparar()
    assert bd.verificar_usuario(demo.USUARIO, demo.CONTRASENA)
    assert bd.obtener_usuario(demo.USUARIO)["rol"] == "administrador"
    assert not bd.listar_pacientes().empty
    assert not bd.listar_doctores().empty


def test_preparar_dos_veces_no_duplica(base_temporal):
    demo.preparar()
    antes = bd.contar_datos()
    demo.preparar()
    assert bd.contar_datos() == antes
    assert len(bd.listar_usuarios()) == 1


def test_despues_de_reiniciar_vuelven_los_datos(base_temporal):
    demo.preparar()
    bd.reiniciar_datos()
    assert bd.listar_pacientes().empty
    demo.preparar()
    assert not bd.listar_pacientes().empty


def _entrar(monkeypatch, modo_demo):
    """Abre la app e inicia sesión como administrador."""
    monkeypatch.setattr(demo, "ACTIVO", modo_demo)
    if not modo_demo:
        bd.crear_usuario(demo.USUARIO, demo.CONTRASENA, rol="administrador")
    app = AppTest.from_file(str(RAIZ / "app.py"), default_timeout=30)
    app.run()
    app.text_input[0].input(demo.USUARIO)
    app.text_input[1].input(demo.CONTRASENA)
    app.button[0].click()
    app.run()
    assert not app.exception
    return app


def test_demo_muestra_el_usuario_en_el_acceso(base_temporal, monkeypatch):
    monkeypatch.setattr(demo, "ACTIVO", True)
    app = AppTest.from_file(str(RAIZ / "app.py"), default_timeout=30)
    app.run()
    # Muestra el acceso con el usuario de la demostración, no la pantalla de crear administrador
    assert any(demo.USUARIO in aviso.value for aviso in app.info)
    assert len(app.text_input) == 2


def test_demo_oculta_mi_cuenta_y_usuarios(base_temporal, monkeypatch):
    app = _entrar(monkeypatch, modo_demo=True)
    for pagina in ("paginas/cuenta.py", "paginas/usuarios.py"):
        with pytest.raises(ValueError):  # la página no está en el menú
            app.switch_page(str(RAIZ / pagina))
    app.switch_page(str(RAIZ / "paginas/reiniciar.py"))
    app.run()
    assert not app.exception


def test_sin_demo_estan_todas_las_paginas(base_temporal, monkeypatch):
    app = _entrar(monkeypatch, modo_demo=False)
    assert not app.sidebar.warning  # sin aviso de demostración
    for pagina in ("paginas/cuenta.py", "paginas/usuarios.py"):
        app.switch_page(str(RAIZ / pagina))
        app.run()
        assert not app.exception
