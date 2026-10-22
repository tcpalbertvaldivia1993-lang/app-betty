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
import sqlite3
import sys
import tomllib
from datetime import datetime
from pathlib import Path

import database as bd

CARPETA_RESPALDOS = Path(__file__).parent / "respaldos_nube"
ARCHIVO_SECRETS = Path(__file__).parent / ".streamlit" / "secrets.toml"

# Orden de copia: primero las tablas a las que apuntan las citas
TABLAS = ["pacientes", "doctores", "citas", "usuarios"]


def obtener_url_nube():
    """La dirección de Neon: variable de entorno, .streamlit/secrets.toml o se pide por teclado."""
    if os.environ.get("DATABASE_URL"):
        return os.environ["DATABASE_URL"]
    if ARCHIVO_SECRETS.exists():
        with open(ARCHIVO_SECRETS, "rb") as archivo:
            url = tomllib.load(archivo).get("DATABASE_URL")
        if url:
            return url
    # getpass no muestra lo que se escribe (la dirección lleva la contraseña)
    return getpass.getpass("Pega la dirección de Neon (postgresql://...) y pulsa Enter: ").strip()


def conectar(url):
    """Conexión directa a Neon. REPEATABLE READ: cada clínica se copia tal como estaba en un instante."""
    import psycopg
    from psycopg.rows import dict_row

    conexion = psycopg.connect(url, row_factory=dict_row)
    conexion.isolation_level = psycopg.IsolationLevel.REPEATABLE_READ
    return conexion


def _esquema_seguro(esquema):
    if not bd.FORMATO_ESQUEMA.fullmatch(esquema):
        raise ValueError(f"Esquema no válido: {esquema!r}")
    return f'"{esquema}"'


def respaldar_clinica(conexion, clinica, destino):
    """Copia una clínica de PostgreSQL a un archivo SQLite nuevo. Devuelve las filas por tabla."""
    esquema = _esquema_seguro(clinica["esquema"])
    bd.crear_tablas(destino)  # mismas tablas que la app con SQLite
    copia = sqlite3.connect(destino)
    filas_por_tabla = {}
    with copia:
        for tabla in TABLAS:
            filas = conexion.execute(f"SELECT * FROM {esquema}.{tabla} ORDER BY id").fetchall()
            if filas:
                columnas = list(filas[0])
                copia.executemany(
                    f"INSERT INTO {tabla} ({', '.join(columnas)}) "
                    f"VALUES ({', '.join('?' * len(columnas))})",
                    [tuple(fila.values()) for fila in filas],
                )
            filas_por_tabla[tabla] = len(filas)
        # Datos para saber de qué clínica es la copia (la app ignora esta tabla)
        copia.execute("CREATE TABLE respaldo_info (clave TEXT PRIMARY KEY, valor TEXT)")
        copia.executemany(
            "INSERT INTO respaldo_info VALUES (?, ?)",
            [
                ("esquema", clinica["esquema"]),
                ("nombre", clinica["nombre"]),
                ("temporal", "1" if clinica["temporal"] else "0"),
                ("fecha_respaldo", datetime.now().isoformat(timespec="seconds")),
            ],
        )
    copia.close()
    return filas_por_tabla


def respaldar(url, carpeta=CARPETA_RESPALDOS, incluir_demos=False):
    """Respalda todas las clínicas en una carpeta nueva con la fecha. Devuelve (carpeta, resumen)."""
    destino = Path(carpeta) / datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    destino.mkdir(parents=True)
    resumen = []
    with conectar(url) as conexion:
        clinicas = conexion.execute(
            """SELECT esquema, nombre, temporal FROM public.clinicas
               WHERE esquema IS NOT NULL AND (%s OR NOT temporal)
               ORDER BY id""",
            (incluir_demos,),
        ).fetchall()
        for clinica in clinicas:
            archivo = destino / f"{clinica['esquema']}.db"
            filas = respaldar_clinica(conexion, clinica, archivo)
            resumen.append({**clinica, "archivo": archivo.name, "filas": filas})
    # Índice de la carpeta: qué clínica hay en cada archivo (sin datos de pacientes)
    (destino / "indice.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return destino, resumen


def main():
    parser = argparse.ArgumentParser(description="Copia de seguridad de las clínicas de la nube.")
    parser.add_argument("--incluir-demos", action="store_true",
                        help="copiar también las clínicas de demostración")
    parser.add_argument("--carpeta", type=Path, default=CARPETA_RESPALDOS,
                        help="carpeta donde guardar las copias (por defecto respaldos_nube/)")
    argumentos = parser.parse_args()

    url = obtener_url_nube()
    if not url.startswith("postgres"):
        sys.exit("Esa no parece una dirección de Neon: debe empezar por postgresql://")
    print("Copiando...")
    carpeta, resumen = respaldar(url, argumentos.carpeta, argumentos.incluir_demos)
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
