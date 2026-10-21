"""Acceso a la base de datos SQLite de la clínica.

Este módulo no usa Streamlit: solo guarda y lee datos.
Así se puede probar con pytest sin abrir la interfaz.
"""

import hashlib
import hmac
import secrets
import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd

from traducciones import ErrorValidacion

# Ruta del archivo de la base de datos (junto a este script)
RUTA_BD = Path(__file__).parent / "clinica.db"

ESTADOS_CITA = ["programada", "atendida", "cancelada", "no_asistio"]


def obtener_conexion(ruta=None):
    """Abre una conexión con las claves foráneas activadas."""
    conexion = sqlite3.connect(ruta or RUTA_BD)
    conexion.row_factory = sqlite3.Row  # permite leer columnas por nombre
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def crear_tablas(ruta=None):
    """Crea las tablas si todavía no existen."""
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


def crear_usuario(usuario, contrasena, rol="personal", ruta=None):
    """Crea un usuario con su contraseña protegida. Devuelve su id."""
    usuario = usuario.strip()
    if not usuario:
        raise ErrorValidacion("err_usuario_obligatorio")
    if rol not in ROLES:
        raise ErrorValidacion("err_rol_invalido", rol=rol)
    _validar_contrasena(contrasena)
    sal = secrets.token_hex(16)  # valor aleatorio distinto para cada usuario
    try:
        with obtener_conexion(ruta) as conexion:
            cursor = conexion.execute(
                "INSERT INTO usuarios (usuario, sal, hash_contrasena, rol) VALUES (?, ?, ?, ?)",
                (usuario, sal, _calcular_hash(contrasena, sal), rol),
            )
            nuevo_id = cursor.lastrowid
        conexion.close()
    except sqlite3.IntegrityError:
        raise ErrorValidacion("err_usuario_existe") from None
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
        tabla = pd.read_sql_query(
            "SELECT id, usuario, rol, activo, creado_en FROM usuarios ORDER BY usuario",
            conexion,
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
        tabla = pd.read_sql_query(
            "SELECT * FROM pacientes ORDER BY apellido, nombre", conexion
        )
    conexion.close()
    return tabla


def buscar_pacientes(texto, ruta=None):
    """Busca pacientes por nombre, apellido o teléfono."""
    patron = f"%{texto.strip()}%"
    with obtener_conexion(ruta) as conexion:
        tabla = pd.read_sql_query(
            """SELECT * FROM pacientes
               WHERE nombre LIKE ? OR apellido LIKE ? OR telefono LIKE ?
                     OR (nombre || ' ' || apellido) LIKE ?
               ORDER BY apellido, nombre""",
            conexion,
            params=(patron, patron, patron, patron),
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
        tabla = pd.read_sql_query(consulta, conexion)
    conexion.close()
    return tabla


def desactivar_doctor(doctor_id, ruta=None):
    """Marca a un doctor como inactivo (no se borra para conservar sus citas)."""
    with obtener_conexion(ruta) as conexion:
        conexion.execute("UPDATE doctores SET activo = 0 WHERE id = ?", (doctor_id,))
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
        tabla = pd.read_sql_query(consulta, conexion, params=parametros)
    conexion.close()
    return tabla


def estadisticas(desde, hasta, ruta=None):
    """Cuenta las citas por doctor y estado en un rango de fechas."""
    with obtener_conexion(ruta) as conexion:
        tabla = pd.read_sql_query(
            """SELECT d.nombre AS doctor, c.estado, COUNT(*) AS total
               FROM citas c
               JOIN doctores d ON d.id = c.doctor_id
               WHERE c.fecha BETWEEN ? AND ?
               GROUP BY d.nombre, c.estado
               ORDER BY d.nombre, c.estado""",
            conexion,
            params=(str(desde), str(hasta)),
        )
    conexion.close()
    return tabla
