"""Pruebas de database.py usando una base de datos temporal."""

import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import database as bd  # noqa: E402

MANANA = date.today() + timedelta(days=1)


@pytest.fixture
def ruta(tmp_path):
    ruta_bd = tmp_path / "prueba.db"
    bd.crear_tablas(ruta_bd)
    return ruta_bd


@pytest.fixture
def datos(ruta):
    """Crea un paciente y un doctor de ejemplo."""
    paciente_id = bd.agregar_paciente("Ana", "López", "555-1234", ruta=ruta)
    doctor_id = bd.agregar_doctor("Dr. Pérez", "Medicina general", ruta=ruta)
    return paciente_id, doctor_id


def test_agregar_y_buscar_paciente(ruta, datos):
    assert len(bd.listar_pacientes(ruta)) == 1
    assert len(bd.buscar_pacientes("ana lóp", ruta)) == 1
    assert len(bd.buscar_pacientes("1234", ruta)) == 1
    assert bd.buscar_pacientes("Carlos", ruta).empty


def test_paciente_sin_nombre_da_error(ruta):
    with pytest.raises(ValueError):
        bd.agregar_paciente("", "López", ruta=ruta)


def test_actualizar_paciente(ruta, datos):
    paciente_id, _ = datos
    bd.actualizar_paciente(paciente_id, "Ana María", "López", "555-0000", ruta=ruta)
    paciente = bd.listar_pacientes(ruta).iloc[0]
    assert paciente["nombre"] == "Ana María"
    assert paciente["telefono"] == "555-0000"


def test_desactivar_doctor(ruta, datos):
    _, doctor_id = datos
    bd.desactivar_doctor(doctor_id, ruta)
    assert bd.listar_doctores(ruta=ruta).empty
    assert len(bd.listar_doctores(solo_activos=False, ruta=ruta)) == 1


def test_agendar_cita(ruta, datos):
    paciente_id, doctor_id = datos
    bd.agendar_cita(paciente_id, doctor_id, MANANA, "09:00", ruta=ruta)
    citas = bd.citas_por_rango(MANANA, MANANA, ruta=ruta)
    assert len(citas) == 1
    assert citas.iloc[0]["paciente"] == "Ana López"
    assert citas.iloc[0]["estado"] == "programada"


def test_choque_de_horario(ruta, datos):
    paciente_id, doctor_id = datos
    bd.agendar_cita(paciente_id, doctor_id, MANANA, "09:00", 30, ruta=ruta)
    # 09:15 se solapa con 09:00-09:30
    with pytest.raises(ValueError, match="horario"):
        bd.agendar_cita(paciente_id, doctor_id, MANANA, "09:15", ruta=ruta)
    # 09:30 justo después: sí se puede
    bd.agendar_cita(paciente_id, doctor_id, MANANA, "09:30", ruta=ruta)


def test_cita_cancelada_libera_horario(ruta, datos):
    paciente_id, doctor_id = datos
    cita_id = bd.agendar_cita(paciente_id, doctor_id, MANANA, "10:00", ruta=ruta)
    bd.cambiar_estado_cita(cita_id, "cancelada", ruta)
    bd.agendar_cita(paciente_id, doctor_id, MANANA, "10:00", ruta=ruta)


def test_fecha_pasada_da_error(ruta, datos):
    paciente_id, doctor_id = datos
    ayer = date.today() - timedelta(days=1)
    with pytest.raises(ValueError, match="pasada"):
        bd.agendar_cita(paciente_id, doctor_id, ayer, "09:00", ruta=ruta)


def test_reprogramar_no_choca_consigo_misma(ruta, datos):
    paciente_id, doctor_id = datos
    cita_id = bd.agendar_cita(paciente_id, doctor_id, MANANA, "11:00", 30, ruta=ruta)
    # Mover 15 minutos se solapa con su propio horario anterior, pero debe permitirse
    bd.reprogramar_cita(cita_id, MANANA, "11:15", ruta)
    assert bd.citas_por_rango(MANANA, MANANA, ruta=ruta).iloc[0]["hora_inicio"] == "11:15"


def test_estado_no_valido(ruta, datos):
    paciente_id, doctor_id = datos
    cita_id = bd.agendar_cita(paciente_id, doctor_id, MANANA, "12:00", ruta=ruta)
    with pytest.raises(ValueError):
        bd.cambiar_estado_cita(cita_id, "perdida", ruta)


def test_estadisticas(ruta, datos):
    paciente_id, doctor_id = datos
    bd.agendar_cita(paciente_id, doctor_id, MANANA, "09:00", ruta=ruta)
    cita_id = bd.agendar_cita(paciente_id, doctor_id, MANANA, "10:00", ruta=ruta)
    bd.cambiar_estado_cita(cita_id, "atendida", ruta)
    tabla = bd.estadisticas(MANANA, MANANA, ruta)
    totales = dict(zip(tabla["estado"], tabla["total"]))
    assert totales == {"atendida": 1, "programada": 1}
