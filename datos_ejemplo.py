"""Llena la base de datos con datos de ejemplo para probar la app.

Uso:  .venv/bin/python datos_ejemplo.py

Solo funciona con la base de datos vacía, para no mezclar datos reales con los de ejemplo.
"""

import random
from datetime import date, timedelta

import database as bd

DOCTORES = [
    ("Dra. Carmen Ruiz", "Medicina general", "555-1001"),
    ("Dr. Luis Fernández", "Pediatría", "555-1002"),
    ("Dra. Sofía Martínez", "Cardiología", "555-1003"),
    ("Dr. Jorge Navarro", "Dermatología", "555-1004"),
]

PACIENTES = [
    ("Ana", "López", "555-2001", "ana.lopez@ejemplo.com", "1985-03-14"),
    ("Carlos", "Gómez", "555-2002", "carlos.gomez@ejemplo.com", "1972-07-02"),
    ("María", "Hernández", "555-2003", "maria.h@ejemplo.com", "1990-11-23"),
    ("José", "Ramírez", "555-2004", "", "1968-01-30"),
    ("Lucía", "Torres", "555-2005", "lucia.torres@ejemplo.com", "2015-05-09"),
    ("Pedro", "Sánchez", "555-2006", "pedro.s@ejemplo.com", "1955-09-17"),
    ("Elena", "Díaz", "555-2007", "", "2001-12-05"),
    ("Miguel", "Castro", "555-2008", "miguel.castro@ejemplo.com", "1979-04-21"),
    ("Isabel", "Morales", "555-2009", "isabel.m@ejemplo.com", "1993-08-11"),
    ("Diego", "Vargas", "555-2010", "", "2018-02-27"),
    ("Rosa", "Jiménez", "555-2011", "rosa.j@ejemplo.com", "1960-06-08"),
    ("Andrés", "Ortiz", "555-2012", "andres.ortiz@ejemplo.com", "1988-10-19"),
]

MOTIVOS = [
    "Consulta general", "Revisión de rutina", "Control de presión",
    "Dolor de cabeza", "Vacunación", "Revisión de análisis",
    "Alergia en la piel", "Control de peso", "Seguimiento", "Fiebre",
]

HORAS = [f"{h:02d}:{m:02d}" for h in range(8, 18) for m in (0, 30)]


def dias_laborables(desde, hasta):
    """Devuelve los días de lunes a viernes entre dos fechas."""
    dia = desde
    while dia <= hasta:
        if dia.weekday() < 5:
            yield dia
        dia += timedelta(days=1)


def cargar():
    """Agrega los datos de ejemplo si la base está vacía.

    Devuelve (doctores, pacientes, citas) agregados, o None si ya había datos.
    """
    bd.crear_tablas()
    if not bd.listar_pacientes().empty or not bd.listar_doctores(solo_activos=False).empty:
        return None

    random.seed(42)  # siempre los mismos datos
    hoy = date.today()

    # Todo con una sola conexión y en una sola transacción: en la nube cada consulta es un
    # viaje de ida y vuelta a Neon, y guardar las citas una por una tardaba casi 2 minutos.
    with bd.obtener_conexion() as conexion:
        doctores_ids = [
            conexion.execute(
                "INSERT INTO doctores (nombre, especialidad, telefono) VALUES (?, ?, ?)", doctor
            ).lastrowid
            for doctor in DOCTORES
        ]
        pacientes_ids = [
            conexion.execute(
                """INSERT INTO pacientes (nombre, apellido, telefono, email, fecha_nacimiento, notas)
                   VALUES (?, ?, ?, ?, ?, '')""",
                paciente,
            ).lastrowid
            for paciente in PACIENTES
        ]

        citas = []
        for dia in dias_laborables(hoy - timedelta(days=14), hoy + timedelta(days=14)):
            for doctor_id in doctores_ids:
                # Entre 1 y 4 citas por doctor y día, en horas distintas
                for hora in sorted(random.sample(HORAS, random.randint(1, 4))):
                    paciente_id = random.choice(pacientes_ids)
                    motivo = random.choice(MOTIVOS)
                    duracion = random.choice([30, 30, 30, 15])  # sin solapes: las horas van de 30 en 30
                    estado = "programada"
                    if dia < hoy:  # el historial ya tiene su resultado
                        estado = random.choices(
                            ["atendida", "no_asistio", "cancelada"], weights=[8, 1, 1]
                        )[0]
                    citas.append(
                        (paciente_id, doctor_id, str(dia), hora, duracion, motivo, estado)
                    )

        # Se insertan directo (sin agendar_cita): las horas ya son distintas y no se solapan
        conexion.executemany(
            """INSERT INTO citas (paciente_id, doctor_id, fecha, hora_inicio,
                                  duracion_min, motivo, estado)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            citas,
        )
    conexion.close()
    total = len(citas)

    return len(doctores_ids), len(pacientes_ids), total


def main():
    cantidades = cargar()
    if cantidades is None:
        print("La base de datos ya tiene datos. No se agregó nada.")
        print("Si quieres empezar de cero, borra clinica.db y vuelve a ejecutar este script.")
        return
    doctores, pacientes, citas = cantidades
    print(f"Listo: {doctores} doctores, {pacientes} pacientes y {citas} citas.")


if __name__ == "__main__":
    main()
