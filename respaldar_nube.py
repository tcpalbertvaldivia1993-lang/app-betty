"""Copia de seguridad de las clínicas guardadas en la nube (PostgreSQL en Neon).

Uso (desde la carpeta del proyecto, en la terminal de Ubuntu/WSL):

    .venv/bin/python respaldar_nube.py                 # todas las clínicas reales
    .venv/bin/python respaldar_nube.py --incluir-demos  # también las de demostración

Guarda cada clínica en su propio archivo SQLite, con el mismo formato que usa la app:
    respaldos_nube/2026-10-22_18-30-00/clinica_3.db
Ese archivo se puede abrir con la app en la computadora (ver README) y entrar con los mismos
usuarios y contraseñas, y se puede volver a subir a la nube con restaurar_nube.py.

La dirección de Neon (DATABASE_URL) se toma de la variable de entorno DATABASE_URL, del archivo
.streamlit/secrets.toml (no se sube a Git) o, si no está en ninguno, se pide al ejecutar.
Las copias tienen datos de pacientes: guárdalas en un lugar protegido, nunca en Git.
"""

import argparse
import getpass
import json
import os
import shutil
import sys
import tomllib
from datetime import datetime
from pathlib import Path

import database as bd

CARPETA_RESPALDOS = Path(__file__).parent / "respaldos_nube"
ARCHIVO_SECRETS = Path(__file__).parent / ".streamlit" / "secrets.toml"

TABLAS = bd.TABLAS_COPIA  # pacientes, doctores, citas y usuarios


def obtener_url_nube(preguntar=True):
    """La dirección de Neon: variable de entorno, .streamlit/secrets.toml o se pide por teclado.

    Con preguntar=False (copia automática, sin nadie delante) devuelve "" si no la encuentra.
    """
    if os.environ.get("DATABASE_URL"):
        return os.environ["DATABASE_URL"]
    if ARCHIVO_SECRETS.exists():
        with open(ARCHIVO_SECRETS, "rb") as archivo:
            url = tomllib.load(archivo).get("DATABASE_URL")
        if url:
            return url
    if not preguntar:
        return ""
    # getpass no muestra lo que se escribe (la dirección lleva la contraseña)
    return getpass.getpass("Pega la dirección de Neon (postgresql://...) y pulsa Enter: ").strip()


class ErrorConexion(Exception):
    """No se pudo conectar a Neon. El mensaje dice qué revisar (nunca muestra la dirección)."""


def revisar_url(url):
    """Errores típicos al pegar la dirección. Devuelve el mensaje para el usuario, o None si se ve bien."""
    if not url:
        return "Falta la dirección de Neon: ponla en .streamlit/secrets.toml (ver README)."
    if not url.startswith("postgres"):
        return "Esa no parece una dirección de Neon: debe empezar por postgresql://"
    if url.count("://") > 1:
        return ("La dirección de Neon está pegada más de una vez seguida. "
                "Déjala una sola vez en .streamlit/secrets.toml.")
    if any(caracter.isspace() for caracter in url):
        return "La dirección de Neon tiene espacios o saltos de línea: cópiala otra vez."
    return None


def conectar(url):
    """Conexión directa a Neon. REPEATABLE READ: cada clínica se copia tal como estaba en un instante."""
    import psycopg
    from psycopg.rows import dict_row

    try:
        conexion = psycopg.connect(url, row_factory=dict_row, connect_timeout=30)
    except psycopg.ProgrammingError:
        # Formato inválido. Sin el detalle: podría llevar trozos de la dirección (y la contraseña)
        raise ErrorConexion(
            "La dirección de Neon no tiene un formato válido. Cópiala otra vez "
            "(Connect → Copy snippet) y ponla una sola vez, entre comillas."
        ) from None
    except psycopg.OperationalError as error:
        raise ErrorConexion(
            "No se pudo conectar a Neon. Revisa la conexión a internet y que la dirección esté "
            f"completa y bien copiada (Connect → Copy snippet).\nDetalle: {error}"
        ) from None
    conexion.isolation_level = psycopg.IsolationLevel.REPEATABLE_READ
    return conexion


def _esquema_seguro(esquema):
    if not bd.FORMATO_ESQUEMA.fullmatch(esquema):
        raise ValueError(f"Esquema no válido: {esquema!r}")
    return f'"{esquema}"'


def respaldar_clinica(conexion, clinica, destino):
    """Copia una clínica de PostgreSQL a un archivo SQLite nuevo. Devuelve las filas por tabla."""
    esquema = _esquema_seguro(clinica["esquema"])
    filas = {
        tabla: conexion.execute(f"SELECT * FROM {esquema}.{tabla} ORDER BY id").fetchall()
        for tabla in TABLAS
    }
    bd.escribir_copia_sqlite(destino, filas, {
        "esquema": clinica["esquema"],
        "nombre": clinica["nombre"],
        "temporal": "1" if clinica["temporal"] else "0",
    })
    return {tabla: len(filas[tabla]) for tabla in TABLAS}


def respaldar(url, carpeta=CARPETA_RESPALDOS, incluir_demos=False):
    """Respalda todas las clínicas en una carpeta nueva con la fecha. Devuelve (carpeta, resumen)."""
    destino = Path(carpeta) / datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    resumen = []
    # Primero se conecta: si la dirección está mal, no se crea ninguna carpeta
    with conectar(url) as conexion:
        clinicas = conexion.execute(
            """SELECT esquema, nombre, temporal FROM public.clinicas
               WHERE esquema IS NOT NULL AND (%s OR NOT temporal)
               ORDER BY id""",
            (incluir_demos,),
        ).fetchall()
        destino.mkdir(parents=True)
        try:
            for clinica in clinicas:
                archivo = destino / f"{clinica['esquema']}.db"
                filas = respaldar_clinica(conexion, clinica, archivo)
                resumen.append({**clinica, "archivo": archivo.name, "filas": filas})
            # Índice de la carpeta: qué clínica hay en cada archivo (sin datos de pacientes)
            (destino / "indice.json").write_text(
                json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except BaseException:
            # Una copia a medias no sirve y confunde: se borra la carpeta
            shutil.rmtree(destino, ignore_errors=True)
            raise
    return destino, resumen


def main():
    parser = argparse.ArgumentParser(description="Copia de seguridad de las clínicas de la nube.")
    parser.add_argument("--incluir-demos", action="store_true",
                        help="copiar también las clínicas de demostración")
    parser.add_argument("--carpeta", type=Path, default=CARPETA_RESPALDOS,
                        help="carpeta donde guardar las copias (por defecto respaldos_nube/)")
    parser.add_argument("--sin-preguntar", action="store_true",
                        help="para la copia automática: no pedir la dirección por teclado")
    argumentos = parser.parse_args()

    print(f"=== Copia del {datetime.now():%Y-%m-%d %H:%M} ===")
    url = obtener_url_nube(preguntar=not argumentos.sin_preguntar)
    problema = revisar_url(url)
    if problema:
        sys.exit(problema)
    print("Copiando...")
    try:
        carpeta, resumen = respaldar(url, argumentos.carpeta, argumentos.incluir_demos)
    except ErrorConexion as error:
        sys.exit(str(error))
    for clinica in resumen:
        filas = clinica["filas"]
        print(f"  {clinica['nombre']} → {clinica['archivo']}: {filas['pacientes']} pacientes, "
              f"{filas['doctores']} doctores, {filas['citas']} citas, {filas['usuarios']} usuarios")
    if not resumen:
        print("  No hay clínicas que copiar.")
    print(f"Listo. Copias guardadas en: {carpeta}")
    print("Tienen datos de pacientes: guárdalas en un lugar protegido.")


if __name__ == "__main__":
    main()
