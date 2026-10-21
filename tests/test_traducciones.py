"""Pruebas de traducciones.py: que no falte ningún texto en ningún idioma."""

import re
import string
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ))
import database as bd  # noqa: E402
from traducciones import IDIOMAS, TEXTOS, ErrorValidacion, traducir  # noqa: E402


def _campos(texto):
    """Nombres de los {campos} que hay que rellenar en un texto."""
    return {campo for _, campo, _, _ in string.Formatter().parse(texto) if campo}


def test_todas_las_claves_tienen_todos_los_idiomas():
    for clave, textos in TEXTOS.items():
        assert set(textos) == set(IDIOMAS), clave


def test_mismos_campos_en_cada_idioma():
    for clave, textos in TEXTOS.items():
        if isinstance(textos["es"], str):
            assert _campos(textos["es"]) == _campos(textos["en"]), clave


def test_claves_usadas_en_el_codigo_existen():
    """Busca t("clave") y ErrorValidacion("clave") en el código y comprueba que existan."""
    archivos = [RAIZ / "app.py", RAIZ / "database.py", *sorted((RAIZ / "paginas").glob("*.py"))]
    patron = re.compile(r"""(?:\bt|ErrorValidacion)\(\s*["'](\w+)["']""")
    usadas = set()
    for archivo in archivos:
        usadas |= set(patron.findall(archivo.read_text(encoding="utf-8")))
    assert usadas, "No se encontró ninguna clave: revisa el patrón"
    faltantes = usadas - set(TEXTOS)
    assert not faltantes, f"Claves sin traducción: {faltantes}"


def test_estados_y_roles_tienen_traduccion():
    for estado in bd.ESTADOS_CITA:
        assert f"estado_{estado}" in TEXTOS
    for rol in bd.ROLES:
        assert f"rol_{rol}" in TEXTOS


def test_traducir_rellena_campos():
    assert traducir("ayuda_contrasena", "es", minimo=8) == "Mínimo 8 caracteres."
    assert traducir("ayuda_contrasena", "en", minimo=8) == "At least 8 characters."


def test_error_validacion_en_los_dos_idiomas(tmp_path):
    ruta = tmp_path / "prueba.db"
    bd.crear_tablas(ruta)
    with pytest.raises(ErrorValidacion) as info:
        bd.crear_usuario("dueno", "corta", ruta=ruta)
    error = info.value
    # str() sigue dando el texto en español, como un ValueError normal
    assert str(error) == "La contraseña debe tener al menos 8 caracteres."
    assert traducir(error.clave, "en", **error.valores) == "The password must have at least 8 characters."
