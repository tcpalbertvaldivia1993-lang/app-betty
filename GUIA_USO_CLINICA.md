# Guía de uso para la clínica - Citas

Actualizada el 22 de octubre de 2026.

La app de citas se usa desde el navegador, sin instalar nada: se abre en [citas-clinica-2026.streamlit.app](https://citas-clinica-2026.streamlit.app) y cada persona entra con su propio usuario y contraseña.

## Qué se necesita

No hay que instalar ningún programa. Basta con:

- Una computadora, tablet o celular con un navegador actualizado (Chrome, Edge, Firefox o Safari).
- Conexión a internet.
- La dirección de la app: [citas-clinica-2026.streamlit.app](https://citas-clinica-2026.streamlit.app)
- Un usuario y una contraseña para cada persona. El primero lo crea el administrador de la clínica (siguiente sección); los demás los crea él desde la app.

## Primera vez: crear la clínica

Esto lo hace una sola vez el administrador (el dueño o encargado de la clínica). Necesita el **código de invitación** que le dio quien administra la app.

1. Abre la dirección de la app y elige la pestaña **Crear clínica**.
2. Rellena el formulario:
   - **Nombre de la clínica**: aparecerá en la barra lateral.
   - **Código de invitación**: escríbelo tal cual, sin comillas.
   - **Usuario**: el nombre con el que entrarás siempre. Debe ser único; si ya existe, la app avisa.
   - **Contraseña** y **Repite la contraseña**: al menos 8 caracteres.
3. No marques **Agregar datos de ejemplo**: eso llena la clínica con doctores y pacientes inventados.
4. Pulsa **Crear clínica**. En unos segundos entras directamente, como administrador.

Los datos quedan guardados: puedes cerrar sesión y volver desde cualquier dispositivo.

## Entrar cada día

1. Abre la dirección de la app.
2. En la pestaña **Iniciar sesión**, escribe tu usuario y tu contraseña y pulsa **Entrar**.
3. Al terminar, pulsa **Cerrar sesión** en la barra lateral, sobre todo en computadoras compartidas.

Para tenerla a mano:

- **En la computadora**: guarda la dirección como favorito, o crea un acceso directo en el escritorio (botón derecho → Nuevo → Acceso directo → pega la dirección → nombre "Clínica - Citas").
- **En el celular**: abre la dirección en el navegador y elige **Agregar a pantalla de inicio**.

El idioma (español o inglés) se cambia con el selector **Idioma / Language** de la barra lateral.

## Dar acceso al personal

Cada persona debe tener su propia cuenta; no compartan usuarios. El administrador las crea en la página **Usuarios**:

1. Escribe el usuario y una contraseña inicial, elige el rol y pulsa crear.
2. Pásale a la persona su usuario y contraseña; ella la cambia después en **Mi cuenta**.
3. Si alguien deja la clínica, **desactiva** su cuenta en Usuarios (se puede reactivar más tarde).

| Rol | Qué puede hacer |
| --- | --- |
| Administrador | Todo: pacientes, doctores, citas, calendario, Usuarios, Copia de seguridad y Reiniciar datos |
| Personal | Todo excepto Usuarios, Copia de seguridad y Reiniciar datos |

Siempre debe quedar al menos un administrador activo.

## Uso diario

Todo se maneja desde el menú de la barra lateral:

| Página | Para qué sirve |
| --- | --- |
| Inicio | Las citas de hoy y de los próximos 7 días |
| Pacientes | Registrar, buscar y editar pacientes |
| Doctores | Registrar doctores, desactivarlos y volver a activarlos |
| Citas | Agendar, reprogramar y cambiar el estado (programada, atendida, cancelada, no asistió) |
| Calendario | Ver las citas por día o por semana, con un gráfico por doctor |
| Mi cuenta | Cambiar la propia contraseña |
| Usuarios | Solo administrador: cuentas del personal |
| Copia de seguridad | Solo administrador: descargar todos los datos (copia completa y Excel) |
| Reiniciar datos | Solo administrador: borra todos los doctores, pacientes y citas |

La app no deja agendar dos citas que se crucen con el mismo doctor ni citas en fechas pasadas. **Reiniciar datos** borra todo: úsalo solo si de verdad quieren empezar de cero.

## Copia de seguridad (una vez por semana)

El administrador descarga una copia de todos los datos de la clínica, por ejemplo cada viernes. Si pasan más de 7 días, la app lo recuerda en la barra lateral.

1. En el menú, entra en **Copia de seguridad**.
2. Pulsa **Preparar la copia** y espera unos segundos.
3. Descarga los dos archivos:
    - **Copia completa (.db)**: todos los datos. Es el archivo que sirve para recuperar la clínica si algo se pierde.
    - **Excel (.xlsx)**: pacientes, doctores y citas, para verlos en Excel.
4. Guárdalos en un USB o en tu nube (Google Drive, OneDrive) y conserva las copias de varias semanas.

Los archivos tienen datos de los pacientes: no los envíes por WhatsApp ni por correo. Si un día hay que recuperar datos, pasa el archivo `.db` a quien administra la app.

## Problemas frecuentes

| Problema | Qué hacer |
| --- | --- |
| Sale un mensaje como "This app has gone to sleep" o un botón "Yes, get this app back up!" | Es normal si nadie la usó en un tiempo. Pulsa el botón y espera alrededor de un minuto. Los datos no se pierden. |
| La primera entrada del día tarda unos segundos | Normal: la base de datos se está "despertando". Espera y vuelve a intentarlo. |
| "Usuario o contraseña incorrectos" | Revisa mayúsculas y espacios. Si no la recuerdas, pide al administrador que la cambie en Usuarios. |
| El administrador olvidó su contraseña | Hay que pedir ayuda a quien administra la app. |
| "El código de invitación no es correcto" | Escríbelo exactamente como te lo dieron, sin comillas ni espacios. |
| "Ese usuario ya existe" | Elige otro nombre de usuario. |
| No se puede agendar una cita | Ese doctor ya tiene una cita a esa hora, o la fecha ya pasó. Elige otra hora o fecha. |
| Se cerró la sesión sola | La cuenta fue desactivada, o se recargó la página. Vuelve a entrar. |

## Seguridad y datos de los pacientes

La app guarda datos de salud en internet, así que conviene cuidarlos:

- Usen contraseñas fuertes (8 caracteres o más, mezclando letras y números) y no las compartan.
- Cierren sesión en computadoras que usan varias personas.
- Desactiven en Usuarios las cuentas de quien deje la clínica.
- Cada clínica solo ve sus propios datos; ninguna otra clínica puede verlos.
- Revisen las leyes de protección de datos de salud de su país (por ejemplo, el consentimiento de los pacientes) antes de cargar datos reales.
- Para dudas o problemas que no estén en esta guía, contacten a quien administra la app.
