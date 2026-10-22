"""Acceso a la base de datos de la clínica.

Funciona con dos motores:
- SQLite (un archivo): el programa para Windows y el desarrollo en la computadora.
- PostgreSQL (Neon, en la nube): la app publicada en internet, con varias clínicas. Se usa
  cuando existe la variable DATABASE_URL. Cada clínica tiene su propio esquema
  (clinica_1, clinica_2...) con las mismas tablas, así nadie ve los datos de otra clínica.

Este módulo no usa Streamlit: solo guarda y lee datos.
Así se puede probar con pytest sin abrir la interfaz.
"""

import atexit
import hashlib
import hmac
import os
import re
import secrets
import sqlite3
from contextvars import ContextVar
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from traducciones import ErrorValidacion

# Ruta del archivo de la base de datos. Por defecto, junto a este script.
# El programa para Windows (lanzador.py) la cambia con la variable de entorno CLINICA_BD.
RUTA_BD = Path(os.environ.get("CLINICA_BD", Path(__file__).parent / "clinica.db"))



def ruta_actual(ruta=None):
    """La ruta del archivo SQLite que se va a usar: la indicada o RUTA_BD."""
    return Path(ruta or RUTA_BD)

ESTADOS_CITA = ["programada", "atendida", "cancelada", "no_asistio"]

# ---------- PostgreSQL (la app publicada en internet) ----------

# Dirección de la base en la nube. En Streamlit Community Cloud se pone en los Secrets.
URL_POSTGRES = os.environ.get("DATABASE_URL")

# La clínica de la sesión (su esquema, p. ej. "clinica_3"). app.py la pone en cada recarga.
esquema_sesion = ContextVar("esquema_sesion", default=None)

# Solo se aceptan nombres de esquema creados por crear_clinica()
FORMATO_ESQUEMA = re.compile(r"clinica_\d+")

_pools = {}  # un grupo de conexiones abiertas por cada URL, para no reconectar en cada consulta


def usa_postgres(ruta=None):
    """True si hay que usar PostgreSQL (si se indica una ruta, siempre es SQLite)."""
    return ruta is None and bool(URL_POSTGRES)


class _Fila(dict):
    """Fila que se lee por nombre (fila["id"]) o por posición (fila[0]), como sqlite3.Row."""

    def __getitem__(self, clave):
        if isinstance(clave, int):
            return list(self.values())[clave]
        return super().__getitem__(clave)


def _fabrica_de_filas(cursor):
    nombres = [columna.name for columna in cursor.description or []]
    return lambda valores: _Fila(zip(nombres, valores))


class _Resultado:
    """Lo que devuelve execute(): filas y, después de un INSERT, el id nuevo."""

    def __init__(self, cursor):
        self._cursor = cursor
        self.columnas = [columna.name for columna in cursor.description or []]

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    def __iter__(self):
        return iter(self._cursor.fetchall())

    @property
    def lastrowid(self):
        # El último id creado en esta conexión (se lee justo después del INSERT)
        return self._cursor.connection.execute("SELECT lastval()").fetchone()[0]


class _ConexionPostgres:
    """Imita lo que este módulo usa de sqlite3 sobre una conexión de PostgreSQL.

    Así las mismas funciones (con ? en las consultas) sirven para los dos motores.
    """

    def __init__(self, esquema):
        self._pool = _obtener_pool()
        self._conexion = self._pool.getconn()
        if esquema is not None and not FORMATO_ESQUEMA.fullmatch(esquema):
            raise ValueError(f"Esquema no válido: {esquema!r}")
        # Solo se ven las tablas de esta clínica (sin clínica, solo las comunes de public)
        self._conexion.execute(
            "SELECT set_config('search_path', %s, false)",
            (f'"{esquema}"' if esquema else "public",),
        )

    @staticmethod
    def _traducir(consulta):
        # sqlite3 usa ? para los valores y psycopg usa %s
        return consulta.replace("%", "%%").replace("?", "%s")

    def execute(self, consulta, parametros=()):
        return _Resultado(self._conexion.execute(self._traducir(consulta), parametros))

    def executemany(self, consulta, filas):
        """Ejecuta la misma consulta para muchas filas, enviándolas juntas (mucho más rápido)."""
        with self._conexion.cursor() as cursor:
            cursor.executemany(self._traducir(consulta), filas)

    def __enter__(self):
        return self

    def __exit__(self, tipo_error, error, traza):
        # Igual que sqlite3: si todo fue bien se guarda, si hubo un error no se guarda nada
        if tipo_error is None:
            self._conexion.commit()
        else:
            self._conexion.rollback()
            self.close()  # si hubo error, quien llamó no llegará a cerrarla

    def close(self):
        if self._conexion is not None:
            self._pool.putconn(self._conexion)
            self._conexion = None


def _obtener_pool():
    if URL_POSTGRES not in _pools:
        from psycopg_pool import ConnectionPool  # solo hace falta en la nube (el .exe no lo trae)

        _pools[URL_POSTGRES] = ConnectionPool(
            URL_POSTGRES, min_size=1, max_size=4, open=True,
            kwargs={"row_factory": _fabrica_de_filas},
            # Neon cierra las conexiones que no se usan: se comprueban antes de usarlas
            check=ConnectionPool.check_connection,
        )
    return _pools[URL_POSTGRES]


@atexit.register
def _cerrar_pools():
    """Cierra las conexiones con la nube al terminar el programa."""
    for pool in _pools.values():
        pool.close()
    _pools.clear()


def _es_duplicado(error):
    """True si el error es por un valor repetido (p. ej. un nombre de usuario que ya existe)."""
    if isinstance(error, sqlite3.IntegrityError):
        return True
    try:
        import psycopg
    except ImportError:
        return False
    return isinstance(error, psycopg.errors.UniqueViolation)


def obtener_conexion(ruta=None):
    """Abre una conexión: SQLite con las claves foráneas activadas, o PostgreSQL en la nube."""
    if usa_postgres(ruta):
        return _ConexionPostgres(esquema_sesion.get())
    conexion = sqlite3.connect(ruta_actual(ruta))
    conexion.row_factory = sqlite3.Row  # permite leer columnas por nombre
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def _leer_tabla(conexion, consulta, parametros=()):
    """Ejecuta una consulta y devuelve el resultado como DataFrame (en los dos motores)."""
    if isinstance(conexion, sqlite3.Connection):
        return pd.read_sql_query(consulta, conexion, params=parametros)
    resultado = conexion.execute(consulta, parametros)
    return pd.DataFrame(resultado.fetchall(), columns=resultado.columnas)


# Tablas de cada clínica en PostgreSQL: las mismas que en SQLite, con los tipos de PostgreSQL
# (también las usa restaurar_nube.py)
TABLAS_POSTGRES = """
    CREATE TABLE IF NOT EXISTS pacientes (
        id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
        nombre TEXT NOT NULL,
        apellido TEXT NOT NULL,
        telefono TEXT,
        email TEXT,
        fecha_nacimiento TEXT,
        notas TEXT,
        creado_en TEXT DEFAULT to_char(now(), 'YYYY-MM-DD HH24:MI:SS')
    );

    CREATE TABLE IF NOT EXISTS doctores (
        id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
        nombre TEXT NOT NULL,
        especialidad TEXT NOT NULL,
        telefono TEXT,
        activo INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS citas (
        id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
        paciente_id INTEGER NOT NULL REFERENCES pacientes(id),
        doctor_id INTEGER NOT NULL REFERENCES doctores(id),
        fecha TEXT NOT NULL,
        hora_inicio TEXT NOT NULL,
        duracion_min INTEGER NOT NULL DEFAULT 30,
        motivo TEXT,
        estado TEXT NOT NULL DEFAULT 'programada'
            CHECK (estado IN ('programada', 'atendida', 'cancelada', 'no_asistio')),
        creado_en TEXT DEFAULT to_char(now(), 'YYYY-MM-DD HH24:MI:SS')
    );

    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
        usuario TEXT NOT NULL UNIQUE,
        sal TEXT NOT NULL,
        hash_contrasena TEXT NOT NULL,
        rol TEXT NOT NULL DEFAULT 'personal' CHECK (rol IN ('administrador', 'personal')),
        activo INTEGER NOT NULL DEFAULT 1,
        creado_en TEXT DEFAULT to_char(now(), 'YYYY-MM-DD HH24:MI:SS')
    );
"""


def crear_tablas(ruta=None):
    """Crea las tablas si todavía no existen."""
    if usa_postgres(ruta):
        with obtener_conexion() as conexion:
            conexion.execute(TABLAS_POSTGRES)
        conexion.close()
        return
    with obtener_conexion(ruta) as conexion:
        conexion.executescript(
            """
            CREATE TABLE IF NOT EXISTS pacientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                apellido TEXT NOT NULL,
                telefono TEXT,
                email TEXT,
                fecha_nacimiento TEXT,
                notas TEXT,
                creado_en TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS doctores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                especialidad TEXT NOT NULL,
                telefono TEXT,
                activo INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS citas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paciente_id INTEGER NOT NULL REFERENCES pacientes(id),
                doctor_id INTEGER NOT NULL REFERENCES doctores(id),
                fecha TEXT NOT NULL,          -- 'YYYY-MM-DD'
                hora_inicio TEXT NOT NULL,    -- 'HH:MM'
                duracion_min INTEGER NOT NULL DEFAULT 30,
                motivo TEXT,
                estado TEXT NOT NULL DEFAULT 'programada'
                    CHECK (estado IN ('programada', 'atendida', 'cancelada', 'no_asistio')),
                creado_en TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT NOT NULL UNIQUE,
                sal TEXT NOT NULL,
                hash_contrasena TEXT NOT NULL,
                rol TEXT NOT NULL DEFAULT 'personal'
                    CHECK (rol IN ('administrador', 'personal')),
                activo INTEGER NOT NULL DEFAULT 1,
                creado_en TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        # Migración: las bases creadas antes de existir los roles no tienen estas columnas.
        # En ellas el único usuario era el propietario, por eso queda como administrador.
        columnas = {fila["name"] for fila in conexion.execute("PRAGMA table_info(usuarios)")}
        if "rol" not in columnas:
            conexion.execute(
                "ALTER TABLE usuarios ADD COLUMN rol TEXT NOT NULL DEFAULT 'administrador'"
            )
        if "activo" not in columnas:
            conexion.execute("ALTER TABLE usuarios ADD COLUMN activo INTEGER NOT NULL DEFAULT 1")
    conexion.close()


# ---------- Usuarios (acceso a la app) ----------

LARGO_MINIMO_CONTRASENA = 8
ROLES = ["administrador", "personal"]


def _calcular_hash(contrasena, sal):
    """Convierte la contraseña en un hash irreversible (no se guarda la contraseña real)."""
    return hashlib.scrypt(
        contrasena.encode("utf-8"), salt=bytes.fromhex(sal), n=2**14, r=8, p=1
    ).hex()


def hay_usuarios(ruta=None):
    """True si ya se creó al menos un usuario."""
    with obtener_conexion(ruta) as conexion:
        cantidad = conexion.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
    conexion.close()
    return cantidad > 0


def _validar_contrasena(contrasena):
    if len(contrasena) < LARGO_MINIMO_CONTRASENA:
        raise ErrorValidacion("err_contrasena_corta", minimo=LARGO_MINIMO_CONTRASENA)


def _validar_usuario_nuevo(usuario, contrasena, rol):
    """Comprueba los datos de un usuario nuevo y devuelve (usuario, sal, hash)."""
    usuario = usuario.strip()
    if not usuario:
        raise ErrorValidacion("err_usuario_obligatorio")
    if rol not in ROLES:
        raise ErrorValidacion("err_rol_invalido", rol=rol)
    _validar_contrasena(contrasena)
    sal = secrets.token_hex(16)  # valor aleatorio distinto para cada usuario
    return usuario, sal, _calcular_hash(contrasena, sal)


def _insertar_usuario(conexion, usuario, sal, hash_contrasena, rol, esquema):
    """Guarda el usuario y, en la nube, anota en el directorio a qué clínica pertenece."""
    cursor = conexion.execute(
        "INSERT INTO usuarios (usuario, sal, hash_contrasena, rol) VALUES (?, ?, ?, ?)",
        (usuario, sal, hash_contrasena, rol),
    )
    nuevo_id = cursor.lastrowid
    if esquema is not None:
        # El nombre de usuario es único en toda la app: así al entrar se sabe su clínica
        conexion.execute(
            "INSERT INTO public.directorio_usuarios (usuario, esquema) VALUES (?, ?)",
            (usuario, esquema),
        )
    return nuevo_id


def crear_usuario(usuario, contrasena, rol="personal", ruta=None):
    """Crea un usuario con su contraseña protegida. Devuelve su id."""
    datos = _validar_usuario_nuevo(usuario, contrasena, rol)
    esquema = esquema_sesion.get() if usa_postgres(ruta) else None
    try:
        with obtener_conexion(ruta) as conexion:
            nuevo_id = _insertar_usuario(conexion, *datos, rol, esquema)
        conexion.close()
    except Exception as error:
        if _es_duplicado(error):
            raise ErrorValidacion("err_usuario_existe") from None
        raise
    return nuevo_id


def obtener_usuario(usuario, ruta=None):
    """Devuelve los datos del usuario (sin la contraseña) o None si no existe."""
    with obtener_conexion(ruta) as conexion:
        fila = conexion.execute(
            "SELECT id, usuario, rol, activo FROM usuarios WHERE usuario = ?",
            (usuario.strip(),),
        ).fetchone()
    conexion.close()
    return dict(fila) if fila else None


def listar_usuarios(ruta=None):
    """Devuelve todos los usuarios como DataFrame (sin datos de contraseña)."""
    with obtener_conexion(ruta) as conexion:
        tabla = _leer_tabla(
            conexion, "SELECT id, usuario, rol, activo, creado_en FROM usuarios ORDER BY usuario"
        )
    conexion.close()
    return tabla


def verificar_usuario(usuario, contrasena, ruta=None):
    """True si el usuario existe, está activo y la contraseña es correcta."""
    with obtener_conexion(ruta) as conexion:
        fila = conexion.execute(
            "SELECT sal, hash_contrasena FROM usuarios WHERE usuario = ? AND activo = 1",
            (usuario.strip(),),
        ).fetchone()
    conexion.close()
    if fila is None:
        return False
    # compare_digest compara sin dar pistas por el tiempo que tarda
    return hmac.compare_digest(_calcular_hash(contrasena, fila["sal"]), fila["hash_contrasena"])


def restablecer_contrasena(usuario_id, contrasena_nueva, ruta=None):
    """Pone una contraseña nueva sin pedir la anterior (lo usa el administrador)."""
    _validar_contrasena(contrasena_nueva)
    sal = secrets.token_hex(16)  # sal nueva en cada cambio
    with obtener_conexion(ruta) as conexion:
        conexion.execute(
            "UPDATE usuarios SET sal = ?, hash_contrasena = ? WHERE id = ?",
            (sal, _calcular_hash(contrasena_nueva, sal), usuario_id),
        )
    conexion.close()


def cambiar_contrasena(usuario, contrasena_actual, contrasena_nueva, ruta=None):
    """Cambia la contraseña si la actual es correcta."""
    if not verificar_usuario(usuario, contrasena_actual, ruta):
        raise ErrorValidacion("err_contrasena_actual")
    _validar_contrasena(contrasena_nueva)
    if contrasena_nueva == contrasena_actual:
        raise ErrorValidacion("err_contrasena_igual")
    restablecer_contrasena(obtener_usuario(usuario, ruta)["id"], contrasena_nueva, ruta)


def cambiar_activo_usuario(usuario_id, activo, ruta=None):
    """Activa o desactiva un usuario. Siempre debe quedar al menos un administrador activo."""
    if not activo:
        with obtener_conexion(ruta) as conexion:
            fila = conexion.execute(
                "SELECT rol FROM usuarios WHERE id = ?", (usuario_id,)
            ).fetchone()
            otros_admins = conexion.execute(
                """SELECT COUNT(*) FROM usuarios
                   WHERE rol = 'administrador' AND activo = 1 AND id != ?""",
                (usuario_id,),
            ).fetchone()[0]
        conexion.close()
        if fila and fila["rol"] == "administrador" and otros_admins == 0:
            raise ErrorValidacion("err_ultimo_admin")

    with obtener_conexion(ruta) as conexion:
        conexion.execute(
            "UPDATE usuarios SET activo = ? WHERE id = ?", (1 if activo else 0, usuario_id)
        )
    conexion.close()


# ---------- Pacientes ----------

def agregar_paciente(nombre, apellido, telefono="", email="",
                     fecha_nacimiento=None, notas="", ruta=None):
    """Guarda un paciente nuevo y devuelve su id."""
    if not nombre.strip() or not apellido.strip():
        raise ErrorValidacion("err_nombre_apellido")
    with obtener_conexion(ruta) as conexion:
        cursor = conexion.execute(
            """INSERT INTO pacientes (nombre, apellido, telefono, email, fecha_nacimiento, notas)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (nombre.strip(), apellido.strip(), telefono, email,
             str(fecha_nacimiento) if fecha_nacimiento else None, notas),
        )
        nuevo_id = cursor.lastrowid
    conexion.close()
    return nuevo_id


def actualizar_paciente(paciente_id, nombre, apellido, telefono="", email="",
                        fecha_nacimiento=None, notas="", ruta=None):
    """Modifica los datos de un paciente existente."""
    if not nombre.strip() or not apellido.strip():
        raise ErrorValidacion("err_nombre_apellido")
    with obtener_conexion(ruta) as conexion:
        conexion.execute(
            """UPDATE pacientes
               SET nombre = ?, apellido = ?, telefono = ?, email = ?,
                   fecha_nacimiento = ?, notas = ?
               WHERE id = ?""",
            (nombre.strip(), apellido.strip(), telefono, email,
             str(fecha_nacimiento) if fecha_nacimiento else None, notas, paciente_id),
        )
    conexion.close()


def listar_pacientes(ruta=None):
    """Devuelve todos los pacientes como DataFrame."""
    with obtener_conexion(ruta) as conexion:
        tabla = _leer_tabla(conexion, "SELECT * FROM pacientes ORDER BY apellido, nombre")
    conexion.close()
    return tabla


def buscar_pacientes(texto, ruta=None):
    """Busca pacientes por nombre, apellido o teléfono."""
    patron = f"%{texto.strip()}%"
    # En SQLite LIKE no distingue mayúsculas; en PostgreSQL hace falta ILIKE
    like = "ILIKE" if usa_postgres(ruta) else "LIKE"
    with obtener_conexion(ruta) as conexion:
        tabla = _leer_tabla(
            conexion,
            f"""SELECT * FROM pacientes
                WHERE nombre {like} ? OR apellido {like} ? OR telefono {like} ?
                      OR (nombre || ' ' || apellido) {like} ?
                ORDER BY apellido, nombre""",
            (patron, patron, patron, patron),
        )
    conexion.close()
    return tabla


# ---------- Doctores ----------

def agregar_doctor(nombre, especialidad, telefono="", ruta=None):
    """Guarda un doctor nuevo y devuelve su id."""
    if not nombre.strip() or not especialidad.strip():
        raise ErrorValidacion("err_nombre_especialidad")
    with obtener_conexion(ruta) as conexion:
        cursor = conexion.execute(
            "INSERT INTO doctores (nombre, especialidad, telefono) VALUES (?, ?, ?)",
            (nombre.strip(), especialidad.strip(), telefono),
        )
        nuevo_id = cursor.lastrowid
    conexion.close()
    return nuevo_id


def listar_doctores(solo_activos=True, ruta=None):
    """Devuelve los doctores como DataFrame."""
    consulta = "SELECT * FROM doctores"
    if solo_activos:
        consulta += " WHERE activo = 1"
    consulta += " ORDER BY nombre"
    with obtener_conexion(ruta) as conexion:
        tabla = _leer_tabla(conexion, consulta)
    conexion.close()
    return tabla


def desactivar_doctor(doctor_id, ruta=None):
    """Marca a un doctor como inactivo (no se borra para conservar sus citas)."""
    with obtener_conexion(ruta) as conexion:
        conexion.execute("UPDATE doctores SET activo = 0 WHERE id = ?", (doctor_id,))
    conexion.close()


def reactivar_doctor(doctor_id, ruta=None):
    """Vuelve a marcar a un doctor como activo, para que aparezca al agendar citas."""
    with obtener_conexion(ruta) as conexion:
        conexion.execute("UPDATE doctores SET activo = 1 WHERE id = ?", (doctor_id,))
    conexion.close()


# ---------- Citas ----------

def _a_minutos(hora):
    """Convierte 'HH:MM' en minutos desde medianoche."""
    horas, minutos = hora.split(":")
    return int(horas) * 60 + int(minutos)


def hay_choque_horario(doctor_id, fecha, hora_inicio, duracion,
                       excluir_id=None, ruta=None):
    """True si el doctor ya tiene otra cita (no cancelada) que se solapa."""
    with obtener_conexion(ruta) as conexion:
        filas = conexion.execute(
            """SELECT id, hora_inicio, duracion_min FROM citas
               WHERE doctor_id = ? AND fecha = ? AND estado != 'cancelada'""",
            (doctor_id, str(fecha)),
        ).fetchall()
    conexion.close()

    inicio_nueva = _a_minutos(hora_inicio)
    fin_nueva = inicio_nueva + duracion
    for fila in filas:
        if excluir_id is not None and fila["id"] == excluir_id:
            continue
        inicio = _a_minutos(fila["hora_inicio"])
        fin = inicio + fila["duracion_min"]
        # Dos intervalos se solapan si cada uno empieza antes de que acabe el otro
        if inicio_nueva < fin and inicio < fin_nueva:
            return True
    return False


def _validar_cita(doctor_id, fecha, hora_inicio, duracion, excluir_id, ruta):
    if date.fromisoformat(str(fecha)) < date.today():
        raise ErrorValidacion("err_fecha_pasada")
    if hay_choque_horario(doctor_id, fecha, hora_inicio, duracion, excluir_id, ruta):
        raise ErrorValidacion("err_choque_horario")


def agendar_cita(paciente_id, doctor_id, fecha, hora_inicio,
                 duracion_min=30, motivo="", ruta=None):
    """Crea una cita nueva si el horario está libre. Devuelve su id."""
    _validar_cita(doctor_id, fecha, hora_inicio, duracion_min, None, ruta)
    with obtener_conexion(ruta) as conexion:
        cursor = conexion.execute(
            """INSERT INTO citas (paciente_id, doctor_id, fecha, hora_inicio, duracion_min, motivo)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (paciente_id, doctor_id, str(fecha), hora_inicio, duracion_min, motivo),
        )
        nuevo_id = cursor.lastrowid
    conexion.close()
    return nuevo_id


def reprogramar_cita(cita_id, fecha, hora_inicio, ruta=None):
    """Cambia la fecha y hora de una cita, comprobando que no choque."""
    with obtener_conexion(ruta) as conexion:
        cita = conexion.execute(
            "SELECT doctor_id, duracion_min FROM citas WHERE id = ?", (cita_id,)
        ).fetchone()
    conexion.close()
    if cita is None:
        raise ErrorValidacion("err_cita_no_existe")

    _validar_cita(cita["doctor_id"], fecha, hora_inicio, cita["duracion_min"], cita_id, ruta)
    with obtener_conexion(ruta) as conexion:
        conexion.execute(
            "UPDATE citas SET fecha = ?, hora_inicio = ?, estado = 'programada' WHERE id = ?",
            (str(fecha), hora_inicio, cita_id),
        )
    conexion.close()


def cambiar_estado_cita(cita_id, estado, ruta=None):
    """Cambia el estado: programada, atendida, cancelada o no_asistio."""
    if estado not in ESTADOS_CITA:
        raise ErrorValidacion("err_estado_invalido", estado=estado)
    with obtener_conexion(ruta) as conexion:
        conexion.execute("UPDATE citas SET estado = ? WHERE id = ?", (estado, cita_id))
    conexion.close()


def citas_por_rango(desde, hasta, doctor_id=None, ruta=None):
    """Devuelve las citas entre dos fechas (incluidas) con nombres de paciente y doctor."""
    consulta = """
        SELECT c.id, c.fecha, c.hora_inicio, c.duracion_min,
               p.nombre || ' ' || p.apellido AS paciente,
               d.nombre AS doctor, d.especialidad,
               c.motivo, c.estado, c.paciente_id, c.doctor_id
        FROM citas c
        JOIN pacientes p ON p.id = c.paciente_id
        JOIN doctores d ON d.id = c.doctor_id
        WHERE c.fecha BETWEEN ? AND ?
    """
    parametros = [str(desde), str(hasta)]
    if doctor_id is not None:
        consulta += " AND c.doctor_id = ?"
        parametros.append(doctor_id)
    consulta += " ORDER BY c.fecha, c.hora_inicio"

    with obtener_conexion(ruta) as conexion:
        tabla = _leer_tabla(conexion, consulta, parametros)
    conexion.close()
    return tabla


def estadisticas(desde, hasta, ruta=None):
    """Cuenta las citas por doctor y estado en un rango de fechas."""
    with obtener_conexion(ruta) as conexion:
        tabla = _leer_tabla(
            conexion,
            """SELECT d.nombre AS doctor, c.estado, COUNT(*) AS total
               FROM citas c
               JOIN doctores d ON d.id = c.doctor_id
               WHERE c.fecha BETWEEN ? AND ?
               GROUP BY d.nombre, c.estado
               ORDER BY d.nombre, c.estado""",
            (str(desde), str(hasta)),
        )
    conexion.close()
    return tabla


# ---------- Reiniciar datos ----------

# Orden de borrado: primero las citas, porque apuntan a doctores y pacientes
TABLAS_DE_DATOS = ["citas", "doctores", "pacientes"]


def contar_datos(ruta=None):
    """Cuántas filas hay en cada tabla de datos. Ej.: {"citas": 212, "doctores": 4, ...}"""
    with obtener_conexion(ruta) as conexion:
        # Los nombres de tabla vienen de la lista fija de arriba, no de lo que escribe el usuario
        conteos = {
            tabla: conexion.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
            for tabla in TABLAS_DE_DATOS
        }
    conexion.close()
    return conteos


def crear_respaldo(ruta=None):
    """Copia la base de datos a la carpeta respaldos/ y devuelve la ruta de la copia."""
    ruta = ruta_actual(ruta)
    carpeta = ruta.parent / "respaldos"
    carpeta.mkdir(exist_ok=True)
    marca = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    destino = carpeta / f"{ruta.stem}_{marca}.db"
    numero = 2
    while destino.exists():  # dos respaldos en el mismo segundo
        destino = carpeta / f"{ruta.stem}_{marca}_{numero}.db"
        numero += 1

    origen = obtener_conexion(ruta)
    copia = sqlite3.connect(destino)
    origen.backup(copia)  # copia segura aunque la base esté en uso
    copia.close()
    origen.close()
    return destino


def reiniciar_datos(ruta=None):
    """Borra todas las citas, doctores y pacientes. Los usuarios se conservan.

    Antes de borrar guarda un respaldo. Devuelve (dónde quedó el respaldo, filas borradas por tabla).
    """
    if usa_postgres(ruta):
        return _reiniciar_datos_postgres()
    respaldo = crear_respaldo(ruta)
    borrados = contar_datos(ruta)
    with obtener_conexion(ruta) as conexion:  # todo o nada: si algo falla, no se borra nada
        for tabla in TABLAS_DE_DATOS:
            conexion.execute(f"DELETE FROM {tabla}")
        # Los números de ID vuelven a empezar desde 1
        conexion.execute(
            "DELETE FROM sqlite_sequence WHERE name IN (?, ?, ?)", TABLAS_DE_DATOS
        )
    conexion.close()
    return respaldo, borrados


def _reiniciar_datos_postgres():
    """Como reiniciar_datos, en la nube: la copia queda en el esquema <clínica>_respaldo."""
    esquema = esquema_sesion.get()
    respaldo = f"{esquema}_respaldo"
    borrados = contar_datos()
    with obtener_conexion() as conexion:  # todo o nada
        # Se guarda solo la última copia (cada reinicio reemplaza la anterior)
        conexion.execute(f'DROP SCHEMA IF EXISTS "{respaldo}" CASCADE')
        conexion.execute(f'CREATE SCHEMA "{respaldo}"')
        for tabla in TABLAS_DE_DATOS:
            conexion.execute(f'CREATE TABLE "{respaldo}".{tabla} AS SELECT * FROM {tabla}')
        # Los números de ID vuelven a empezar desde 1
        conexion.execute(f"TRUNCATE {', '.join(TABLAS_DE_DATOS)} RESTART IDENTITY")
    conexion.close()
    return respaldo, borrados


# ---------- Clínicas (solo en la nube, con PostgreSQL) ----------

HORAS_DEMO = 24  # las clínicas de demostración se borran tras este tiempo sin uso


# Tablas comunes a todas las clínicas (también las usa restaurar_nube.py)
TABLAS_COMUNES_POSTGRES = """
    CREATE TABLE IF NOT EXISTS public.clinicas (
        id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
        esquema TEXT UNIQUE,
        nombre TEXT NOT NULL,
        temporal BOOLEAN NOT NULL DEFAULT FALSE,
        ultimo_uso TIMESTAMPTZ NOT NULL DEFAULT now(),
        creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS public.directorio_usuarios (
        usuario TEXT PRIMARY KEY,
        esquema TEXT NOT NULL
    );
"""


def preparar_nube():
    """Crea las tablas comunes a todas las clínicas, si todavía no existen."""
    with obtener_conexion() as conexion:
        conexion.execute(TABLAS_COMUNES_POSTGRES)
    conexion.close()


def crear_clinica(nombre, usuario, contrasena, temporal=False):
    """Crea una clínica nueva con su administrador. Devuelve su esquema (p. ej. "clinica_3").

    Todo pasa en una sola transacción: si algo falla (p. ej. el usuario ya existe), no queda nada a medias.
    """
    nombre = nombre.strip()
    if not nombre:
        raise ErrorValidacion("err_nombre_clinica")
    datos = _validar_usuario_nuevo(usuario, contrasena, "administrador")
    token = esquema_sesion.set(None)  # las tablas comunes están en public
    try:
        with obtener_conexion() as conexion:
            id_clinica = conexion.execute(
                "INSERT INTO public.clinicas (nombre, temporal) VALUES (?, ?) RETURNING id",
                (nombre, temporal),
            ).fetchone()[0]
            esquema = f"clinica_{id_clinica}"
            conexion.execute("UPDATE public.clinicas SET esquema = ? WHERE id = ?", (esquema, id_clinica))
            conexion.execute(f'CREATE SCHEMA "{esquema}"')
            conexion.execute(f"""SELECT set_config('search_path', '"{esquema}"', true)""")
            conexion.execute(TABLAS_POSTGRES)
            _insertar_usuario(conexion, *datos, "administrador", esquema)
        conexion.close()
    except Exception as error:
        if _es_duplicado(error):
            raise ErrorValidacion("err_usuario_existe") from None
        raise
    finally:
        esquema_sesion.reset(token)
    return esquema


def esquema_de_usuario(usuario):
    """El esquema de la clínica a la que pertenece el usuario, o None si no existe."""
    token = esquema_sesion.set(None)
    try:
        with obtener_conexion() as conexion:
            fila = conexion.execute(
                "SELECT esquema FROM public.directorio_usuarios WHERE usuario = ?",
                (usuario.strip(),),
            ).fetchone()
        conexion.close()
    finally:
        esquema_sesion.reset(token)
    return fila["esquema"] if fila else None


def usar_clinica(esquema):
    """Datos de la clínica ({"nombre", "temporal"}) o None si ya no existe.

    También anota que se está usando (como mucho una vez por hora), para que las
    clínicas de demostración en uso no se borren.
    """
    token = esquema_sesion.set(None)
    try:
        with obtener_conexion() as conexion:
            fila = conexion.execute(
                "SELECT nombre, temporal FROM public.clinicas WHERE esquema = ?", (esquema,)
            ).fetchone()
            conexion.execute(
                """UPDATE public.clinicas SET ultimo_uso = now()
                   WHERE esquema = ? AND ultimo_uso < now() - interval '1 hour'""",
                (esquema,),
            )
        conexion.close()
    finally:
        esquema_sesion.reset(token)
    return dict(fila) if fila else None


def borrar_clinicas_temporales_viejas(horas=HORAS_DEMO):
    """Borra las clínicas de demostración que llevan más de `horas` sin usarse. Devuelve cuántas."""
    token = esquema_sesion.set(None)
    try:
        with obtener_conexion() as conexion:
            viejas = [
                fila["esquema"] for fila in conexion.execute(
                    """SELECT esquema FROM public.clinicas
                       WHERE temporal AND ultimo_uso < now() - make_interval(hours => ?)""",
                    (horas,),
                )
            ]
            for esquema in viejas:
                if not FORMATO_ESQUEMA.fullmatch(esquema):
                    continue
                conexion.execute(f'DROP SCHEMA IF EXISTS "{esquema}" CASCADE')
                conexion.execute(f'DROP SCHEMA IF EXISTS "{esquema}_respaldo" CASCADE')
                conexion.execute("DELETE FROM public.directorio_usuarios WHERE esquema = ?", (esquema,))
                conexion.execute("DELETE FROM public.clinicas WHERE esquema = ?", (esquema,))
        conexion.close()
    finally:
        esquema_sesion.reset(token)
    return len(viejas)
