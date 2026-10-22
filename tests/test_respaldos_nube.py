"""Pruebas de respaldar_nube.py y restaurar_nube.py (necesitan CLINICA_PG_PRUEBAS, ver conftest.py)."""

import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import database as bd  # noqa: E402
import datos_ejemplo  # noqa: E402
import respaldar_nube  # noqa: E402
import restaurar_nube  # noqa: E402
from conftest import URL_PRUEBAS  # noqa: E402


@pytest.fixture
def clinicas(postgres):
    """Dos clínicas reales (una con datos de ejemplo) y una demo."""
    sol = bd.crear_clinica("Clínica Sol", "sol_admin", "secreta123")
    bd.esquema_sesion.set(sol)
    datos_ejemplo.cargar()
    bd.crear_usuario("recepcion", "secreta123")
    luna = bd.crear_clinica("Clínica Luna", "luna_admin", "secreta123")
    bd.esquema_sesion.set(luna)
    bd.agregar_paciente("Ana", "López")
    demo = bd.crear_clinica("Clínica de prueba", "visitante", "secreta123", temporal=True)
    return {"sol": sol, "luna": luna, "demo": demo}


def _respaldar(tmp_path, **opciones):
    carpeta, resumen = respaldar_nube.respaldar(URL_PRUEBAS, tmp_path, **opciones)
    return carpeta, {clinica["esquema"]: clinica for clinica in resumen}


def test_respalda_cada_clinica_real_en_sqlite(clinicas, tmp_path):
    carpeta, resumen = _respaldar(tmp_path)
    assert set(resumen) == {clinicas["sol"], clinicas["luna"]}  # sin la demo
    assert resumen[clinicas["sol"]]["filas"] == {
        "pacientes": 12, "doctores": 4, "citas": 212, "usuarios": 2,
    }
    assert (carpeta / "indice.json").exists()

    # La copia funciona con la app en SQLite: mismos datos y mismas contraseñas
    copia = carpeta / f"{clinicas['sol']}.db"
    assert bd.contar_datos(copia) == {"citas": 212, "doctores": 4, "pacientes": 12}
    assert bd.verificar_usuario("sol_admin", "secreta123", copia)
    assert bd.verificar_usuario("recepcion", "secreta123", copia)


def test_incluir_demos(clinicas, tmp_path):
    _, resumen = _respaldar(tmp_path, incluir_demos=True)
    assert clinicas["demo"] in resumen


def test_restaurar_deja_la_clinica_como_en_la_copia(clinicas, tmp_path):
    carpeta, _ = _respaldar(tmp_path)
    sol = clinicas["sol"]

    # Después de la copia: se borran datos, se cambia una contraseña y se crea un usuario
    bd.esquema_sesion.set(sol)
    bd.reiniciar_datos()
    bd.cambiar_contrasena("sol_admin", "secreta123", "otra-clave-1")
    bd.crear_usuario("nuevo", "secreta123")

    assert restaurar_nube.restaurar(URL_PRUEBAS, carpeta / f"{sol}.db") == sol
    bd.esquema_sesion.set(sol)
    assert bd.contar_datos() == {"citas": 212, "doctores": 4, "pacientes": 12}
    assert bd.verificar_usuario("sol_admin", "secreta123")  # la contraseña de la copia
    assert bd.esquema_de_usuario("nuevo") is None  # el usuario creado después ya no existe
    assert bd.esquema_de_usuario("recepcion") == sol
    # Los ids nuevos siguen después de los de la copia
    assert bd.agregar_paciente("Nuevo", "Paciente") == 13
    # Lo que había antes de restaurar quedó guardado aparte
    with bd.obtener_conexion() as conexion:
        antes = conexion.execute(f'SELECT count(*) FROM "{sol}_antes_de_restaurar".usuarios').fetchone()[0]
    conexion.close()
    assert antes == 3
    # La otra clínica no cambió
    bd.esquema_sesion.set(clinicas["luna"])
    assert len(bd.listar_pacientes()) == 1


def test_las_citas_siguen_validandose_despues_de_restaurar(clinicas, tmp_path):
    carpeta, _ = _respaldar(tmp_path)
    restaurar_nube.restaurar(URL_PRUEBAS, carpeta / f"{clinicas['luna']}.db")
    bd.esquema_sesion.set(clinicas["luna"])
    [paciente_id] = bd.listar_pacientes()["id"].tolist()
    doctor_id = bd.agregar_doctor("Dr. Pérez", "Medicina general")
    manana = date.today() + timedelta(days=1)
    bd.agendar_cita(paciente_id, doctor_id, manana, "09:00")
    with pytest.raises(ValueError):
        bd.agendar_cita(paciente_id, doctor_id, manana, "09:00")


def test_restaurar_una_clinica_borrada(clinicas, tmp_path):
    carpeta, _ = _respaldar(tmp_path)
    luna = clinicas["luna"]
    with bd.obtener_conexion() as conexion:  # la clínica desaparece de la nube
        conexion.execute(f'DROP SCHEMA "{luna}" CASCADE')
        conexion.execute("DELETE FROM public.directorio_usuarios WHERE esquema = ?", (luna,))
        conexion.execute("DELETE FROM public.clinicas WHERE esquema = ?", (luna,))
    conexion.close()

    nuevo = restaurar_nube.restaurar(URL_PRUEBAS, carpeta / f"{luna}.db")
    assert nuevo != luna  # se crea otra vez, con otro número
    assert bd.esquema_de_usuario("luna_admin") == nuevo
    assert bd.usar_clinica(nuevo)["nombre"] == "Clínica Luna"
    bd.esquema_sesion.set(nuevo)
    assert bd.verificar_usuario("luna_admin", "secreta123")
    assert bd.listar_pacientes()["nombre"].tolist() == ["Ana"]


def test_no_restaura_si_el_usuario_es_de_otra_clinica(clinicas, tmp_path):
    carpeta, _ = _respaldar(tmp_path)
    sol = clinicas["sol"]
    bd.esquema_sesion.set(sol)
    with bd.obtener_conexion() as conexion:  # "recepcion" pasa a otra clínica
        conexion.execute("DELETE FROM usuarios WHERE usuario = 'recepcion'")
        conexion.execute(
            "UPDATE public.directorio_usuarios SET esquema = ? WHERE usuario = 'recepcion'",
            (clinicas["luna"],),
        )
    conexion.close()
    bd.agregar_paciente("Solo", "Ahora")

    with pytest.raises(restaurar_nube.ErrorRestaurar, match="recepcion"):
        restaurar_nube.restaurar(URL_PRUEBAS, carpeta / f"{sol}.db")
    # No cambió nada: sigue el paciente nuevo y no se creó la copia de seguridad previa
    bd.esquema_sesion.set(sol)
    assert len(bd.listar_pacientes()) == 13
    with bd.obtener_conexion() as conexion:
        copia_previa = conexion.execute(
            "SELECT 1 FROM pg_namespace WHERE nspname = ?", (f"{sol}_antes_de_restaurar",)
        ).fetchone()
    conexion.close()
    assert copia_previa is None


def test_archivo_que_no_es_una_copia(tmp_path):
    otro = tmp_path / "otro.db"
    bd.crear_tablas(otro)  # una base de la app, pero no hecha con respaldar_nube.py
    with pytest.raises(restaurar_nube.ErrorRestaurar):
        restaurar_nube.leer_copia(otro)
    with pytest.raises(restaurar_nube.ErrorRestaurar):
        restaurar_nube.leer_copia(tmp_path / "no_existe.db")
    texto = tmp_path / "notas.txt"
    texto.write_text("esto no es una base de datos", encoding="utf-8")
    with pytest.raises(restaurar_nube.ErrorRestaurar):
        restaurar_nube.leer_copia(texto)


def test_direccion_de_neon(monkeypatch, tmp_path):
    secrets = tmp_path / "secrets.toml"
    monkeypatch.setattr(respaldar_nube, "ARCHIVO_SECRETS", secrets)
    monkeypatch.setenv("DATABASE_URL", "postgresql://desde-entorno")
    assert respaldar_nube.obtener_url_nube() == "postgresql://desde-entorno"

    monkeypatch.delenv("DATABASE_URL")
    secrets.write_text('DATABASE_URL = "postgresql://desde-secrets"\n', encoding="utf-8")
    assert respaldar_nube.obtener_url_nube() == "postgresql://desde-secrets"

    secrets.unlink()  # sin variable ni archivo: se pide por teclado (sin mostrarla)
    monkeypatch.setattr(respaldar_nube.getpass, "getpass", lambda texto: " postgresql://tecleada ")
    assert respaldar_nube.obtener_url_nube() == "postgresql://tecleada"


def test_si_no_conecta_no_crea_carpeta(tmp_path):
    """Con una dirección equivocada no queda ninguna carpeta vacía."""
    url_mala = "postgresql://nadie@127.0.0.1:1/no_existe?connect_timeout=2"
    with pytest.raises(respaldar_nube.ErrorConexion, match="No se pudo conectar"):
        respaldar_nube.respaldar(url_mala, tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_si_falla_a_medias_borra_la_carpeta(clinicas, tmp_path, monkeypatch):
    def falla(*argumentos):
        raise RuntimeError("se cortó la conexión")

    monkeypatch.setattr(respaldar_nube, "respaldar_clinica", falla)
    with pytest.raises(RuntimeError):
        respaldar_nube.respaldar(URL_PRUEBAS, tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_la_copia_de_la_app_se_puede_restaurar(clinicas, tmp_path):
    """El archivo que descarga el administrador en la app sirve para restaurar_nube.py."""
    sol = clinicas["sol"]
    bd.esquema_sesion.set(sol)
    copia = tmp_path / "copia_clinica.db"
    bd.exportar_sqlite(copia, {"esquema": sol, "nombre": "Clínica Sol", "temporal": "0"})
    bd.reiniciar_datos()

    assert restaurar_nube.restaurar(URL_PRUEBAS, copia) == sol
    bd.esquema_sesion.set(sol)
    assert bd.contar_datos() == {"citas": 212, "doctores": 4, "pacientes": 12}


def test_copia_automatica_sin_direccion(monkeypatch, tmp_path):
    """Sin nadie delante no se pide la dirección: el script termina con un mensaje claro."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(respaldar_nube, "ARCHIVO_SECRETS", tmp_path / "no_existe.toml")
    assert respaldar_nube.obtener_url_nube(preguntar=False) == ""
    monkeypatch.setattr(sys, "argv", ["respaldar_nube.py", "--sin-preguntar", "--carpeta", str(tmp_path)])
    with pytest.raises(SystemExit, match="secrets.toml"):
        respaldar_nube.main()
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("url, aviso", [
    ("", "Falta la dirección"),
    ("https://neon.tech", "debe empezar por postgresql://"),
    ("postgresql://a:CLAVE@h/db?x=1postgresql://a:CLAVE@h/db?x=1", "más de una vez"),
    ("postgresql://a:CLAVE@h/db ?x=1", "espacios"),
])
def test_revisar_url_avisa_de_errores_al_pegar(url, aviso):
    mensaje = respaldar_nube.revisar_url(url)
    assert aviso in mensaje
    assert "CLAVE" not in mensaje


def test_revisar_url_acepta_una_direccion_correcta():
    url = "postgresql://usuario:clave@ep-algo.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
    assert respaldar_nube.revisar_url(url) is None


def test_formato_invalido_no_muestra_la_direccion():
    """El caso real: la dirección pegada dos veces daba un error técnico largo."""
    url = "postgresql://a:CLAVE@h/db?channel_binding=requirepostgresql://a:CLAVE@h/db?channel_binding=require"
    with pytest.raises(respaldar_nube.ErrorConexion) as error:
        respaldar_nube.conectar(url)
    assert "formato válido" in str(error.value)
    assert "CLAVE" not in str(error.value)


def test_la_copia_automatica_explica_la_direccion_duplicada(monkeypatch, tmp_path):
    secrets = tmp_path / "secrets.toml"
    secrets.write_text('DATABASE_URL = "postgresql://a:CLAVE@h/db?x=1postgresql://a:CLAVE@h/db?x=1"\n',
                       encoding="utf-8")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(respaldar_nube, "ARCHIVO_SECRETS", secrets)
    monkeypatch.setattr(sys, "argv", ["respaldar_nube.py", "--sin-preguntar", "--carpeta", str(tmp_path / "c")])
    with pytest.raises(SystemExit, match="más de una vez") as salida:
        respaldar_nube.main()
    assert "CLAVE" not in str(salida.value)
    assert not (tmp_path / "c").exists()
