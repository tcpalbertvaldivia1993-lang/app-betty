# App de citas de la clínica

Aplicación web hecha con **Streamlit** y **SQLite** para gestionar las citas de los pacientes.

## Funciones

- **Acceso con usuario y contraseña**: la primera vez que se abre la app pide crear la cuenta
  del administrador (el propietario de la clínica). Después, siempre pide iniciar sesión.
  La contraseña no se guarda tal cual, sino como un hash (scrypt con sal).
- **Mi cuenta**: cambiar la contraseña (pide la contraseña actual).
- **Usuarios** (solo administradores): crear cuentas para el personal, desactivarlas o
  reactivarlas y restablecer su contraseña. Hay dos roles:
  - `administrador`: puede hacer todo, incluida la gestión de usuarios.
  - `personal`: usa toda la app excepto la página Usuarios.

  Siempre debe quedar al menos un administrador activo.
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

Si alguien del personal olvida su contraseña, el administrador la restablece en **Usuarios**.
Si la olvida el único administrador, hay que borrar todas las filas de la tabla `usuarios`
en `clinica.db` (también las del personal); al abrir la app pedirá crear el administrador otra vez.

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
| `app.py` | Entrada: pide usuario y contraseña y arma el menú de páginas |
| `database.py` | Tablas y funciones para guardar/leer datos y verificar usuarios |
| `paginas/` | Una página por sección (solo se ven con la sesión iniciada) |
| `datos_ejemplo.py` | Llena la base de datos con datos de prueba |
| `tests/` | Pruebas de `database.py` |
