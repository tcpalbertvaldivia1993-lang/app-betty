"""Restaura en la nube (PostgreSQL en Neon) una clínica desde su copia de respaldar_nube.py.

Uso (desde la carpeta del proyecto, en la terminal de Ubuntu/WSL):

    .venv/bin/python restaurar_nube.py respaldos_nube/2026-10-22_18-30-00/clinica_3.db

- Si la clínica todavía existe en la nube, sus pacientes, doctores, citas y usuarios se
  reemplazan por los de la copia. Antes se guarda lo que había en el esquema
  <clínica>_antes_de_restaurar (solo la última vez), por si hay que volver atrás.
- Si la clínica ya no existe (o es otra base de Neon), se crea de nuevo con los datos de la copia.
- Los usuarios y sus contraseñas vuelven a ser los de la copia.
- Pide escribir RESTAURAR para confirmar. Todo pasa en una transacción: si algo falla, no cambia nada.

La dirección de Neon se obtiene igual que en respaldar_nube.py.
"""

import argparse
import sqlite3
import sys
from pathlib import Path

import database as bd
from respaldar_nube import TABLAS, conectar, obtener_url_nube

PALABRA_CONFIRMAR = "RESTAURAR"


class ErrorRestaurar(Exception):
    """Algo impide restaurar la copia (se explica en el mensaje)."""


def leer_copia(archivo):
    """Lee una copia: (información de la clínica, {tabla: [filas como dict]})."""
    archivo = Path(archivo)
    if not archivo.exists():
        raise ErrorRestaurar(f"No existe el archivo {archivo}")
    copia = sqlite3.connect(f"file:{archivo}?mode=ro", uri=True)  # solo lectura
    copia.row_factory = sqlite3.Row
    try:
        info = dict(copia.execute("SELECT clave, valor FROM respaldo_info").fetchall())
    except sqlite3.DatabaseError:  # no es SQLite, o es una base sin respaldo_info
        copia.close()
        raise ErrorRestaurar(f"{archivo} no es una copia hecha con respaldar_nube.py") from None
    datos = {
        tabla: [dict(fila) for fila in copia.execute(f"SELECT * FROM {tabla} ORDER BY id")]
        for tabla in TABLAS
    }
    copia.close()
    return info, datos


def _cuantos(conexion, esquema):
    return {
        tabla: conexion.execute(f'SELECT count(*) AS n FROM "{esquema}".{tabla}').fetchone()["n"]
        for tabla in TABLAS
    }


def estado_actual(url, info):
    """Cuántas filas tiene ahora esa clínica en la nube, o None si ya no existe."""
    with conectar(url) as conexion:
        existe = conexion.execute(
            "SELECT 1 FROM public.clinicas WHERE esquema = %s", (info["esquema"],)
        ).fetchone()
        return _cuantos(conexion, info["esquema"]) if existe else None


def restaurar(url, archivo):
    """Sube la copia a la nube. Devuelve el esquema de la clínica restaurada."""
    info, datos = leer_copia(archivo)
    esquema = info["esquema"]
    if not bd.FORMATO_ESQUEMA.fullmatch(esquema):
        raise ErrorRestaurar(f"Esquema no válido en la copia: {esquema!r}")

    with conectar(url) as conexion:  # una sola transacción: todo o nada
        conexion.execute(bd.TABLAS_COMUNES_POSTGRES)  # por si es una base de Neon nueva
        existe = conexion.execute(
            "SELECT 1 FROM public.clinicas WHERE esquema = %s", (esquema,)
        ).fetchone()
        if existe:
            # Lo que había se guarda aparte (solo la última restauración)
            antes = f"{esquema}_antes_de_restaurar"
            conexion.execute(f'DROP SCHEMA IF EXISTS "{antes}" CASCADE')
            conexion.execute(f'CREATE SCHEMA "{antes}"')
            for tabla in TABLAS:
                conexion.execute(f'CREATE TABLE "{antes}".{tabla} AS SELECT * FROM "{esquema}".{tabla}')
            conexion.execute(
                f'TRUNCATE "{esquema}".citas, "{esquema}".doctores, "{esquema}".pacientes, '
                f'"{esquema}".usuarios RESTART IDENTITY'
            )
        else:
            # La clínica ya no existe: se crea otra vez (puede quedar con otro número)
            id_clinica = conexion.execute(
                "INSERT INTO public.clinicas (nombre, temporal) VALUES (%s, %s) RETURNING id",
                (info["nombre"], info.get("temporal") == "1"),
            ).fetchone()["id"]
            esquema = f"clinica_{id_clinica}"
            conexion.execute("UPDATE public.clinicas SET esquema = %s WHERE id = %s", (esquema, id_clinica))
            conexion.execute(f'CREATE SCHEMA "{esquema}"')
            conexion.execute(f"""SELECT set_config('search_path', '"{esquema}"', true)""")
            conexion.execute(bd.TABLAS_POSTGRES)

        for tabla in TABLAS:
            filas = datos[tabla]
            if filas:
                columnas = list(filas[0])
                with conexion.cursor() as cursor:
                    cursor.executemany(
                        f'INSERT INTO "{esquema}".{tabla} ({", ".join(columnas)}) '
                        f'VALUES ({", ".join(["%s"] * len(columnas))})',
                        [tuple(fila.values()) for fila in filas],
                    )
            # Los ids nuevos siguen después del mayor de la copia
            conexion.execute(
                f"""SELECT setval(pg_get_serial_sequence('"{esquema}".{tabla}', 'id'),
                                  COALESCE((SELECT max(id) FROM "{esquema}".{tabla}), 1),
                                  (SELECT count(*) > 0 FROM "{esquema}".{tabla}))"""
            )

        # Directorio de usuarios: el de la copia (los usuarios creados después dejan de existir)
        conexion.execute("DELETE FROM public.directorio_usuarios WHERE esquema = %s", (esquema,))
        for usuario in datos["usuarios"]:
            ocupado = conexion.execute(
                "SELECT esquema FROM public.directorio_usuarios WHERE usuario = %s",
                (usuario["usuario"],),
            ).fetchone()
            if ocupado:
                raise ErrorRestaurar(
                    f"El usuario {usuario['usuario']!r} ahora pertenece a otra clínica "
                    f"({ocupado['esquema']}). No se restauró nada."
                )
            conexion.execute(
                "INSERT INTO public.directorio_usuarios (usuario, esquema) VALUES (%s, %s)",
                (usuario["usuario"], esquema),
            )
    return esquema


def main():
    parser = argparse.ArgumentParser(description="Restaura una clínica en la nube desde su copia.")
    parser.add_argument("archivo", type=Path, help="la copia, p. ej. respaldos_nube/.../clinica_3.db")
    argumentos = parser.parse_args()

    try:
        info, datos = leer_copia(argumentos.archivo)
        url = obtener_url_nube()
        if not url.startswith("postgres"):
            sys.exit("Esa no parece una dirección de Neon: debe empezar por postgresql://")
        ahora = estado_actual(url, info)
    except ErrorRestaurar as error:
        sys.exit(f"Error: {error}")

    print(f"Clínica: {info['nombre']} ({info['esquema']}), copia del {info['fecha_respaldo']}")
    print("  En la copia:", ", ".join(f"{len(datos[t])} {t}" for t in TABLAS))
    if ahora is None:
        print("  En la nube: la clínica no existe; se creará de nuevo.")
    else:
        print("  En la nube ahora:", ", ".join(f"{ahora[t]} {t}" for t in TABLAS))
        print("  Lo que hay ahora se reemplazará (se guarda antes una copia en la nube).")
    if input(f"Escribe {PALABRA_CONFIRMAR} para continuar: ").strip() != PALABRA_CONFIRMAR:
        sys.exit("Cancelado: no se cambió nada.")

    try:
        esquema = restaurar(url, argumentos.archivo)
    except ErrorRestaurar as error:
        sys.exit(f"Error: {error}")
    print(f"Listo: {info['nombre']} restaurada en {esquema}.")
    print("Si la app estaba abierta, cierra sesión y vuelve a entrar.")


if __name__ == "__main__":
    main()
