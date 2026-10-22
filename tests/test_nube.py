"""Pruebas del modo nube (nube.py): varias clínicas en PostgreSQL, con datos que se guardan.

Necesitan CLINICA_PG_PRUEBAS (ver conftest.py); sin ella se saltan.
"""

import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ))
import database as bd  # noqa: E402
import nube  # noqa: E402

CODIGO = "codigo-de-prueba"


@pytest.fixture
def app_nube(postgres, monkeypatch):
    """La app en modo nube, con el código de invitación de prueba."""
    monkeypatch.setattr(nube, "ACTIVO", True)
    monkeypatch.setattr(nube, "CODIGO_INVITACION", CODIGO)


def _abrir():
    app = AppTest.from_file(str(RAIZ / "app.py"), default_timeout=60)
    app.run()
    assert not app.exception
    return app


def _enviar(app, boton):
    [b for b in app.button if b.label == boton][0].click()
    app.run()
    assert not app.exception


def _crear_clinica(app, nombre, usuario, codigo=CODIGO, ejemplos=False):
    app.text_input(key="clinica_nombre").input(nombre)
    app.text_input(key="clinica_codigo").input(codigo)
    app.text_input(key="clinica_usuario").input(usuario)
    app.text_input(key="clinica_contrasena").input("secreta123")
    app.text_input(key="clinica_repetir").input("secreta123")
    if ejemplos:
        app.checkbox(key="clinica_ejemplos").check()
    _enviar(app, "Crear clínica")


def _entrar(app, usuario, contrasena="secreta123"):
    app.text_input(key="login_usuario").input(usuario)
    app.text_input(key="login_contrasena").input(contrasena)
    _enviar(app, "Entrar")


def _con_sesion(app):
    """True si hay sesión iniciada. Además elige su clínica para leer datos desde la prueba
    (AppTest ejecuta la app en otro hilo, así que la prueba no ve su esquema_sesion)."""
    if "esquema" in app.session_state:
        bd.esquema_sesion.set(app.session_state["esquema"])
    return any(b.label == "Cerrar sesión" for b in app.sidebar.button)


def test_crear_clinica_y_volver_a_entrar(app_nube):
    app = _abrir()
    _crear_clinica(app, "Clínica Sol", "sol_admin")
    assert _con_sesion(app)
    assert any("Clínica Sol" in m.value for m in app.sidebar.markdown)

    # Agrega un paciente en su clínica y cierra la sesión
    bd.agregar_paciente("Ana", "López")
    _enviar(app, "Cerrar sesión")
    assert not _con_sesion(app)

    # Otro día, desde otro dispositivo (sesión nueva): el paciente sigue ahí
    otra = _abrir()
    _entrar(otra, "sol_admin")
    assert _con_sesion(otra)
    assert bd.listar_pacientes()["nombre"].tolist() == ["Ana"]


def test_codigo_de_invitacion_incorrecto(app_nube):
    app = _abrir()
    _crear_clinica(app, "Clínica Falsa", "falso", codigo="otro")
    assert not _con_sesion(app)
    assert any("código de invitación" in e.value for e in app.error)
    assert bd.esquema_de_usuario("falso") is None


def test_sin_codigo_configurado_no_se_crean_clinicas(app_nube, monkeypatch):
    monkeypatch.setattr(nube, "CODIGO_INVITACION", "")
    app = _abrir()
    assert any("no se pueden crear clínicas" in i.value for i in app.info)
    assert not nube.codigo_valido("")


def test_clinicas_separadas(app_nube):
    sol = _abrir()
    _crear_clinica(sol, "Clínica Sol", "sol_admin", ejemplos=True)
    assert _con_sesion(sol)
    assert len(bd.listar_pacientes()) == 12  # datos de ejemplo

    luna = _abrir()
    _crear_clinica(luna, "Clínica Luna", "luna_admin")
    assert _con_sesion(luna)
    assert bd.listar_pacientes().empty  # no ve los pacientes de Clínica Sol

    # El mismo nombre de usuario no se puede repetir, aunque sea en otra clínica
    otra = _abrir()
    _crear_clinica(otra, "Clínica Otra", "sol_admin")
    assert any("ya existe" in e.value for e in otra.error)


def test_el_personal_entra_en_su_clinica(app_nube):
    app = _abrir()
    _crear_clinica(app, "Clínica Sol", "sol_admin", ejemplos=True)
    assert _con_sesion(app)
    bd.crear_usuario("recepcion", "secreta123")  # lo crea el administrador en Usuarios

    personal = _abrir()
    _entrar(personal, "recepcion")
    assert _con_sesion(personal)
    assert len(bd.listar_pacientes()) == 12
    # El personal no ve las páginas de administrador
    with pytest.raises(ValueError):
        personal.switch_page(str(RAIZ / "paginas/usuarios.py"))


def test_contrasena_incorrecta(app_nube):
    app = _abrir()
    _crear_clinica(app, "Clínica Sol", "sol_admin")
    otra = _abrir()
    _entrar(otra, "sol_admin", "mala-clave")
    assert not _con_sesion(otra)
    _entrar(otra, "no_existe")
    assert not _con_sesion(otra)


def test_demo_temporal(app_nube):
    app = _abrir()
    app.text_input(key="demo_usuario").input("visitante")
    app.text_input(key="demo_contrasena").input("secreta123")
    app.text_input(key="demo_repetir").input("secreta123")
    _enviar(app, "Crear clínica de prueba")
    assert _con_sesion(app)
    assert any("demostración" in w.value for w in app.sidebar.warning)
    assert len(bd.listar_pacientes()) == 12


def test_se_borran_solo_las_demos_viejas(postgres):
    demo = bd.crear_clinica("Demo vieja", "visitante", "secreta123", temporal=True)
    real = bd.crear_clinica("Clínica real", "dueno", "secreta123")
    with bd.obtener_conexion() as conexion:  # las dos llevan 2 días sin usarse
        conexion.execute("UPDATE public.clinicas SET ultimo_uso = now() - interval '2 days'")
    conexion.close()

    assert bd.borrar_clinicas_temporales_viejas() == 1
    assert bd.usar_clinica(demo) is None
    assert bd.esquema_de_usuario("visitante") is None
    assert bd.usar_clinica(real) == {"nombre": "Clínica real", "temporal": False}


def test_sesion_de_una_demo_borrada_se_cierra(app_nube):
    app = _abrir()
    app.text_input(key="demo_usuario").input("visitante")
    app.text_input(key="demo_contrasena").input("secreta123")
    app.text_input(key="demo_repetir").input("secreta123")
    _enviar(app, "Crear clínica de prueba")
    assert _con_sesion(app)

    bd.borrar_clinicas_temporales_viejas(horas=0)
    app.run()
    assert not app.exception
    assert not _con_sesion(app)


def test_reiniciar_guarda_respaldo_en_la_nube(postgres):
    esquema = bd.crear_clinica("Clínica Sol", "dueno", "secreta123")
    bd.esquema_sesion.set(esquema)
    bd.agregar_doctor("Dr. Pérez", "Medicina general")

    respaldo, borrados = bd.reiniciar_datos()
    assert respaldo == f"{esquema}_respaldo"
    assert borrados == {"citas": 0, "doctores": 1, "pacientes": 0}
    assert bd.contar_datos() == {"citas": 0, "doctores": 0, "pacientes": 0}
    assert bd.verificar_usuario("dueno", "secreta123")  # los usuarios se conservan
    with bd.obtener_conexion() as conexion:
        copia = conexion.execute(f'SELECT nombre FROM "{respaldo}".doctores').fetchall()
    conexion.close()
    assert [fila["nombre"] for fila in copia] == ["Dr. Pérez"]
    assert bd.agregar_doctor("Dr. Nuevo", "Pediatría") == 1  # los ID vuelven a empezar


def test_sin_nube_funciona_como_antes(tmp_path, monkeypatch):
    """Sin DATABASE_URL (programa para Windows): pantalla Bienvenido y una sola clínica en SQLite."""
    monkeypatch.setattr(bd, "URL_POSTGRES", None)
    monkeypatch.setattr(nube, "ACTIVO", False)
    monkeypatch.setattr(bd, "RUTA_BD", tmp_path / "clinica.db")
    app = _abrir()
    assert len(app.text_input) == 3  # usuario, contraseña y repetir
    assert not app.tabs  # sin las pestañas de la nube
    app.text_input[0].input("dueno")
    app.text_input[1].input("secreta123")
    app.text_input[2].input("secreta123")
    _enviar(app, "Crear administrador")
    assert _con_sesion(app)
    assert bd.verificar_usuario("dueno", "secreta123")


def test_lee_los_secrets_de_streamlit(monkeypatch):
    """En Streamlit Community Cloud los valores pueden estar solo en st.secrets."""
    monkeypatch.delenv("CODIGO_INVITACION", raising=False)
    monkeypatch.setattr(nube.st, "secrets", {"CODIGO_INVITACION": "desde-secrets"})
    assert nube._secreto("CODIGO_INVITACION") == "desde-secrets"
    monkeypatch.setenv("CODIGO_INVITACION", "desde-entorno")
    assert nube._secreto("CODIGO_INVITACION") == "desde-entorno"
    assert nube._secreto("NO_EXISTE") is None
