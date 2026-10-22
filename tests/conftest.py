"""Preparación común de las pruebas.

Las pruebas con PostgreSQL solo se ejecutan si la variable CLINICA_PG_PRUEBAS tiene la dirección
de una base de PRUEBAS (su nombre debe contener "prueba"), porque cada prueba la vacía.
Ejemplo:  CLINICA_PG_PRUEBAS=postgresql://postgres@127.0.0.1:54329/clinica_pruebas .venv/bin/python -m pytest
Sin la variable, esas pruebas se saltan y solo se prueba SQLite.
"""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import database as bd  # noqa: E402

URL_PRUEBAS = os.environ.get("CLINICA_PG_PRUEBAS")


def _vaciar_postgres():
    """Borra todas las clínicas y las tablas comunes de la base de pruebas."""
    import psycopg

    with psycopg.connect(URL_PRUEBAS, autocommit=True) as conexion:
        esquemas = conexion.execute(
            "SELECT nspname FROM pg_namespace WHERE nspname LIKE 'clinica\\_%'"
        ).fetchall()
        for (esquema,) in esquemas:
            conexion.execute(f'DROP SCHEMA "{esquema}" CASCADE')
        conexion.execute("DROP TABLE IF EXISTS public.clinicas, public.directorio_usuarios")


@pytest.fixture
def postgres(monkeypatch):
    """Hace que la app use la base de pruebas de PostgreSQL, vacía."""
    if not URL_PRUEBAS:
        pytest.skip("Sin CLINICA_PG_PRUEBAS: se saltan las pruebas con PostgreSQL")
    assert "prueba" in URL_PRUEBAS.rsplit("/", 1)[-1], "CLINICA_PG_PRUEBAS debe ser una base de pruebas"
    monkeypatch.setattr(bd, "URL_POSTGRES", URL_PRUEBAS)
    _vaciar_postgres()
    bd.preparar_nube()
    yield
    bd.esquema_sesion.set(None)  # AppTest corre en este mismo hilo: que no afecte a otras pruebas


def clinica_vacia(nombre="Pruebas"):
    """Crea una clínica sin usuarios y la deja como la clínica de la sesión. Devuelve su esquema."""
    esquema = bd.crear_clinica(nombre, f"admin_{nombre.lower()}", "secreta123")
    bd.esquema_sesion.set(esquema)
    with bd.obtener_conexion() as conexion:
        conexion.execute("DELETE FROM usuarios")
        conexion.execute("DELETE FROM public.directorio_usuarios WHERE esquema = ?", (esquema,))
    conexion.close()
    return esquema
