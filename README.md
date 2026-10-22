# App de citas de la clínica

Aplicación web hecha con **Streamlit** para gestionar las citas de los pacientes. Guarda los datos
en **SQLite** (instalada en una clínica) o en **PostgreSQL** (publicada en internet, con varias clínicas).

**[▶️ Abrir la app en línea](https://citas-clinica-2026.streamlit.app)**: cualquiera puede probar la
demostración sin instalar nada (ver [En internet](#en-internet-streamlit-community-cloud--neon)).

## Funciones

- **Idioma**: español o inglés, con el selector «🌐 Idioma / Language» de la barra lateral
  (también en la pantalla de inicio de sesión). Se traducen menús, botones, mensajes, nombres
  de columnas, estados de las citas, roles y formato de fechas. Lo que escribe cada persona
  (nombres, motivos de consulta) se guarda y se muestra tal cual.
- **Acceso con usuario y contraseña**: la primera vez que se abre la app pide crear la cuenta
  del administrador (el propietario de la clínica). Después, siempre pide iniciar sesión.
  La contraseña no se guarda tal cual, sino como un hash (scrypt con sal).
- **Mi cuenta**: cambiar la contraseña (pide la contraseña actual).
- **Usuarios** (solo administradores): crear cuentas para el personal, desactivarlas o
  reactivarlas y restablecer su contraseña. Hay dos roles:
  - `administrador`: puede hacer todo, incluida la gestión de usuarios.
  - `personal`: usa toda la app excepto la página Usuarios.

  Siempre debe quedar al menos un administrador activo.
- **Reiniciar datos** (solo administradores): borra todos los doctores, pacientes y citas para
  empezar de cero; los usuarios se conservan. Pide marcar una casilla y escribir `BORRAR`
  (en inglés, `DELETE`). Antes de borrar guarda una copia en `respaldos/`.
- **En internet**: varias clínicas, cada una con sus datos guardados, y una demostración temporal (ver más abajo).
- **Inicio**: resumen de las citas de hoy y de los próximos 7 días.
- **Pacientes**: registrar, buscar y editar pacientes.
- **Doctores**: registrar doctores, desactivarlos y volver a activarlos.
- **Citas**: agendar, reprogramar y cambiar el estado (programada, atendida, cancelada, no asistió).
  La app no deja agendar dos citas que se solapen con el mismo doctor ni citas en fechas pasadas.
- **Calendario**: ver citas por día o semana y un gráfico por doctor y estado.

## Instalar en la clínica (Windows)

Para usar la app en una clínica, se construye un programa para Windows (`ClinicaCitas.exe`) que
no necesita Python. Una PC hace de servidor y las demás PCs y celulares entran por el navegador.

- **Construir el ZIP** (en una PC con Windows y Python 3): ejecutar `construir_windows.bat`.
  Crea `dist\ClinicaCitas-windows.zip`.
- **Instalarlo y usarlo en la clínica**: ver [INSTALACION_CLINICA.md](INSTALACION_CLINICA.md).

## En internet (Streamlit Community Cloud + Neon)

La app se publica gratis en [Streamlit Community Cloud](https://share.streamlit.io) y guarda los
datos en una base **PostgreSQL** gratuita de [Neon](https://neon.tech). El disco de Streamlit se borra
en cada reinicio, por eso los datos van en Neon. Cada clínica tiene su propio esquema de PostgreSQL
(`clinica_1`, `clinica_2`...), así que ninguna ve los datos de otra.

Al abrir la app hay tres pestañas (`nube.py`):
- **Iniciar sesión**: el administrador y el personal de cada clínica entran con su usuario y
  contraseña, desde cualquier dispositivo. Los datos se conservan.
- **Crear clínica**: crea una clínica y su administrador. Pide el **código de invitación**, para que
  solo las clínicas a las que se lo des puedan registrarse. Puede empezar vacía o con datos de ejemplo.
- **Probar la demostración**: crea una clínica de prueba con datos de ejemplo, sin código. Se borra
  sola tras 24 horas sin uso.

Los nombres de usuario son únicos en toda la app. Al reiniciar los datos, la copia de seguridad queda
en el esquema `clinica_N_respaldo` (solo la última).

### Publicarla

1. **Neon**: crea una cuenta en https://neon.tech y un proyecto (región *AWS US East*, cerca de los
   servidores de Streamlit). En **Connect** copia la *connection string* (`postgresql://...`).
2. **Streamlit**: en https://share.streamlit.io, **Create app** con este repositorio, la rama `main`
   y el archivo `app.py`. En **Advanced settings → Secrets** (o, si ya existe, ⋮ → **Settings → Secrets**):

   ```toml
   DATABASE_URL = "postgresql://..."
   CODIGO_INVITACION = "elige-un-codigo-dificil"
   ```
3. Para cambiar el código de invitación, cámbialo en los Secrets. Las clínicas ya creadas no se ven
   afectadas. Sin `CODIGO_INVITACION` no se pueden crear clínicas nuevas (la demostración sigue funcionando).

**Datos reales de salud**: guardar datos de pacientes en internet exige cumplir las leyes de
protección de datos de cada país. Usa contraseñas fuertes y una cuenta por persona.

### Probarla en tu computadora

Con cualquier PostgreSQL (por ejemplo, una rama de pruebas en Neon):

```bash
DATABASE_URL=postgresql://... CODIGO_INVITACION=prueba .venv/bin/streamlit run app.py
```

## Instalación

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt -r requirements-dev.txt
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

### Recuperar un respaldo

Cada vez que se reinician los datos se guarda una copia en `respaldos/` (por ejemplo
`respaldos/clinica_2026-10-21_17-42-34.db`). Para volver a ella, con la app detenida:

```bash
cp respaldos/clinica_2026-10-21_17-42-34.db clinica.db
```

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

Así se prueba solo SQLite. Para probar también PostgreSQL, indica una base **de pruebas** (su
nombre debe contener `prueba`, porque las pruebas la vacían):

```bash
CLINICA_PG_PRUEBAS=postgresql://.../clinica_pruebas .venv/bin/python -m pytest
```

## Archivos

| Archivo | Qué hace |
|---|---|
| `app.py` | Entrada: pide usuario y contraseña y arma el menú de páginas |
| `database.py` | Tablas y funciones para guardar/leer datos y verificar usuarios |
| `paginas/` | Una página por sección (solo se ven con la sesión iniciada) |
| `respaldos/` | Copias de seguridad creadas al reiniciar los datos (no se suben a Git) |
| `lanzador.py` | Punto de entrada de `ClinicaCitas.exe`: arranca el servidor y abre el navegador |
| `construir_windows.bat` | Construye el `.exe` y el ZIP para Windows |
| `INSTALACION_CLINICA.md` | Guía de instalación para la clínica (va dentro del ZIP) |
| `traducciones.py` | Textos de la app en español e inglés |
| `datos_ejemplo.py` | Llena la base de datos con datos de prueba |
| `nube.py` | Modo nube: pantalla de acceso con varias clínicas y la demostración |
| `tests/` | Pruebas de `database.py` (SQLite y PostgreSQL), de las traducciones y del modo nube |
