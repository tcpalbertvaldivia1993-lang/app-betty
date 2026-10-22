# App de citas de la clínica

Aplicación web hecha con **Streamlit** y **SQLite** para gestionar las citas de los pacientes.

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
- **Modo demostración**: para publicarla en internet (ver más abajo).
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

## Demostración en internet (Streamlit Community Cloud)

Para que cualquier persona pueda probar la app desde su navegador, sin instalar nada, se publica
gratis en [Streamlit Community Cloud](https://share.streamlit.io) en **modo demostración**:

1. Entra en https://share.streamlit.io con tu cuenta de GitHub y pulsa **Create app**.
2. Elige este repositorio, la rama `main` y el archivo `app.py`.
3. En **Advanced settings**: elige Python 3.12 o más nuevo, y en **Secrets** escribe:

   ```toml
   MODO_DEMO = "1"
   ```
4. Pulsa **Deploy**. La dirección será algo como `https://<nombre>.streamlit.app`.

En modo demostración (`demo.py`), **cada visita tiene su propia copia de la app**, privada y temporal:
- La primera vez aparece la pantalla **Bienvenido** para crear su propio administrador, igual que
  al instalar la app en una clínica. Ya hay datos de ejemplo para probar.
- Nadie ve los datos de las demás visitas.
- La dirección lleva un código (`?demo=...`): al recargar la página (F5) no se pierde nada, y
  guardándola como favorito se puede volver más tarde. Sin el código, empieza una visita nueva.
- Las visitas que llevan más de 24 horas sin usarse se borran solas. También se borra todo
  cuando Streamlit reinicia el servidor. **No sirve para datos reales de pacientes**: para la
  clínica, usa la instalación en Windows.

Para probar el modo demostración en tu computadora:

```bash
MODO_DEMO=1 .venv/bin/streamlit run app.py
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
| `demo.py` | Modo demostración para internet: una base de datos privada por visita |
| `tests/` | Pruebas de `database.py`, de las traducciones y del modo demostración |
