# App de citas de la clínica

Aplicación web hecha con **Streamlit** y **SQLite** para gestionar las citas de los pacientes.

## Funciones

- **Inicio**: resumen de las citas de hoy y de los próximos 7 días.
- **Pacientes**: registrar, buscar y editar pacientes.
- **Doctores**: registrar doctores y desactivarlos.
- **Citas**: agendar, reprogramar y cambiar el estado (programada, atendida, cancelada, no asistió).
  La app no deja agendar dos citas que se solapen con el mismo doctor ni citas en fechas pasadas.
- **Calendario**: ver citas por día o semana y un gráfico por doctor y estado.

## Instalación

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Uso

```bash
.venv/bin/streamlit run app.py
```

Se abre en el navegador en http://localhost:8501. Los datos se guardan en `clinica.db`
(se crea solo la primera vez).

### Datos de ejemplo

Para probar la app con datos (4 doctores, 12 pacientes y citas de las últimas 2 semanas y las próximas 2):

```bash
.venv/bin/python datos_ejemplo.py
```

Solo funciona con la base de datos vacía. Para volver a empezar, borra `clinica.db`.

## Pruebas

```bash
.venv/bin/python -m pytest
```

## Archivos

| Archivo | Qué hace |
|---|---|
| `app.py` | Página de inicio |
| `database.py` | Tablas y funciones para guardar/leer datos |
| `pages/` | Una página por sección (Streamlit crea el menú automáticamente) |
| `tests/` | Pruebas de `database.py` |
