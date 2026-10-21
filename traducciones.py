"""Textos de la app en español e inglés.

Cada clave tiene su texto en los dos idiomas. Las páginas usan t("clave") y obtienen
el texto en el idioma elegido en la barra lateral. Para agregar un texto nuevo,
agrega su clave en TEXTOS con "es" y "en".
"""

IDIOMAS = {"es": "Español", "en": "English"}
IDIOMA_POR_DEFECTO = "es"

TEXTOS = {
    # ---------- General ----------
    "titulo_pestana": {"es": "Clínica - Citas", "en": "Clinic - Appointments"},
    "si": {"es": "Sí", "en": "Yes"},
    "no": {"es": "No", "en": "No"},
    "formato_fecha": {"es": "DD/MM/YYYY", "en": "MM/DD/YYYY"},  # para st.date_input
    "strftime_fecha": {"es": "%d/%m/%Y", "en": "%m/%d/%Y"},  # para mostrar fechas
    "dias_semana": {
        "es": ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"],
        "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    },
    "error_no_coinciden": {"es": "Las contraseñas no coinciden.", "en": "The passwords do not match."},
    "ayuda_contrasena": {
        "es": "Mínimo {minimo} caracteres.",
        "en": "At least {minimo} characters.",
    },

    # ---------- Menú ----------
    "pag_login": {"es": "Iniciar sesión", "en": "Log in"},
    "pag_crear_admin": {"es": "Crear administrador", "en": "Create administrator"},
    "pag_inicio": {"es": "Inicio", "en": "Home"},
    "pag_pacientes": {"es": "Pacientes", "en": "Patients"},
    "pag_doctores": {"es": "Doctores", "en": "Doctors"},
    "pag_citas": {"es": "Citas", "en": "Appointments"},
    "pag_calendario": {"es": "Calendario", "en": "Calendar"},
    "pag_cuenta": {"es": "Mi cuenta", "en": "My account"},
    "pag_usuarios": {"es": "Usuarios", "en": "Users"},
    "pag_reiniciar": {"es": "Reiniciar datos", "en": "Reset data"},
    "sesion": {"es": "👤 Sesión: **{usuario}** ({rol})", "en": "👤 Signed in: **{usuario}** ({rol})"},
    "boton_cerrar_sesion": {"es": "Cerrar sesión", "en": "Log out"},

    # ---------- Acceso ----------
    "bienvenida_titulo": {"es": "🏥 Bienvenido", "en": "🏥 Welcome"},
    "bienvenida_texto": {
        "es": "Es la primera vez que se abre la app. Crea la cuenta del administrador (propietario de la clínica).",
        "en": "This is the first time the app is opened. Create the administrator account (the clinic owner).",
    },
    "campo_usuario": {"es": "Usuario", "en": "Username"},
    "campo_contrasena": {"es": "Contraseña", "en": "Password"},
    "campo_repetir_contrasena": {"es": "Repite la contraseña", "en": "Repeat the password"},
    "boton_crear_admin": {"es": "Crear administrador", "en": "Create administrator"},
    "login_titulo": {"es": "🔒 Iniciar sesión", "en": "🔒 Log in"},
    "boton_entrar": {"es": "Entrar", "en": "Log in"},
    "error_login": {"es": "Usuario o contraseña incorrectos.", "en": "Incorrect username or password."},

    # ---------- Valores guardados (se guardan en español y se muestran traducidos) ----------
    "estado_programada": {"es": "programada", "en": "scheduled"},
    "estado_atendida": {"es": "atendida", "en": "attended"},
    "estado_cancelada": {"es": "cancelada", "en": "cancelled"},
    "estado_no_asistio": {"es": "no asistió", "en": "no-show"},
    "rol_administrador": {"es": "administrador", "en": "administrator"},
    "rol_personal": {"es": "personal", "en": "staff"},

    # ---------- Nombres de columnas en las tablas ----------
    "col_id": {"es": "ID", "en": "ID"},
    "col_fecha": {"es": "Fecha", "en": "Date"},
    "col_hora_inicio": {"es": "Hora", "en": "Time"},
    "col_duracion_min": {"es": "Duración (min)", "en": "Duration (min)"},
    "col_paciente": {"es": "Paciente", "en": "Patient"},
    "col_doctor": {"es": "Doctor", "en": "Doctor"},
    "col_motivo": {"es": "Motivo", "en": "Reason"},
    "col_estado": {"es": "Estado", "en": "Status"},
    "col_nombre": {"es": "Nombre", "en": "First name"},
    "col_apellido": {"es": "Apellido", "en": "Last name"},
    "col_telefono": {"es": "Teléfono", "en": "Phone"},
    "col_email": {"es": "Email", "en": "Email"},
    "col_fecha_nacimiento": {"es": "Fecha de nacimiento", "en": "Date of birth"},
    "col_especialidad": {"es": "Especialidad", "en": "Specialty"},
    "col_activo": {"es": "Activo", "en": "Active"},
    "col_usuario": {"es": "Usuario", "en": "Username"},
    "col_rol": {"es": "Rol", "en": "Role"},
    "col_creado_en": {"es": "Creado el", "en": "Created on"},

    # ---------- Inicio ----------
    "inicio_titulo": {"es": "🏥 Citas de la clínica", "en": "🏥 Clinic appointments"},
    "inicio_ayuda": {
        "es": "Usa el menú de la izquierda para gestionar pacientes, doctores y citas.",
        "en": "Use the menu on the left to manage patients, doctors and appointments.",
    },
    "metrica_citas_hoy": {"es": "Citas hoy", "en": "Today's appointments"},
    "metrica_pendientes": {"es": "Pendientes", "en": "Pending"},
    "metrica_atendidas": {"es": "Atendidas", "en": "Attended"},
    "metrica_canceladas": {"es": "Canceladas", "en": "Cancelled"},
    "agenda_hoy": {"es": "Agenda de hoy ({fecha})", "en": "Today's schedule ({fecha})"},
    "sin_citas_hoy": {"es": "No hay citas para hoy.", "en": "No appointments today."},
    "proximos_7": {"es": "Próximos 7 días", "en": "Next 7 days"},
    "sin_citas_proximas": {
        "es": "No hay citas programadas para los próximos días.",
        "en": "No appointments scheduled for the coming days.",
    },

    # ---------- Pacientes ----------
    "pacientes_titulo": {"es": "🧑 Pacientes", "en": "🧑 Patients"},
    "tab_nuevo_paciente": {"es": "Nuevo paciente", "en": "New patient"},
    "tab_buscar_editar": {"es": "Buscar y editar", "en": "Search and edit"},
    "campo_nombre": {"es": "Nombre *", "en": "First name *"},
    "campo_apellido": {"es": "Apellido *", "en": "Last name *"},
    "campo_telefono": {"es": "Teléfono", "en": "Phone"},
    "campo_email": {"es": "Email", "en": "Email"},
    "campo_nacimiento": {"es": "Fecha de nacimiento", "en": "Date of birth"},
    "campo_notas": {"es": "Notas", "en": "Notes"},
    "boton_guardar_paciente": {"es": "Guardar paciente", "en": "Save patient"},
    "paciente_guardado": {"es": "Paciente {nombre} guardado.", "en": "Patient {nombre} saved."},
    "buscar_pacientes": {
        "es": "Buscar por nombre, apellido o teléfono",
        "en": "Search by first name, last name or phone",
    },
    "sin_pacientes": {"es": "No se encontraron pacientes.", "en": "No patients found."},
    "editar_paciente": {"es": "Editar paciente", "en": "Edit patient"},
    "campo_paciente": {"es": "Paciente", "en": "Patient"},
    "boton_guardar_cambios": {"es": "Guardar cambios", "en": "Save changes"},
    "cambios_guardados": {"es": "Cambios guardados.", "en": "Changes saved."},

    # ---------- Doctores ----------
    "doctores_titulo": {"es": "🩺 Doctores", "en": "🩺 Doctors"},
    "nuevo_doctor": {"es": "Nuevo doctor", "en": "New doctor"},
    "campo_nombre_doctor": {"es": "Nombre *", "en": "Name *"},
    "campo_especialidad": {"es": "Especialidad *", "en": "Specialty *"},
    "boton_guardar_doctor": {"es": "Guardar doctor", "en": "Save doctor"},
    "doctor_guardado": {"es": "{nombre} guardado.", "en": "{nombre} saved."},
    "lista_doctores": {"es": "Lista de doctores", "en": "Doctor list"},
    "mostrar_inactivos": {"es": "Mostrar también los inactivos", "en": "Also show inactive doctors"},
    "sin_doctores": {"es": "Todavía no hay doctores registrados.", "en": "No doctors registered yet."},
    "desactivar_doctor": {"es": "Desactivar doctor", "en": "Deactivate doctor"},
    "desactivar_doctor_ayuda": {
        "es": "El doctor deja de aparecer al agendar citas, pero se conservan sus citas anteriores.",
        "en": "The doctor no longer appears when booking, but their past appointments are kept.",
    },
    "campo_doctor": {"es": "Doctor", "en": "Doctor"},
    "boton_desactivar": {"es": "Desactivar", "en": "Deactivate"},
    "sin_doctores_activos": {
        "es": "No hay doctores activos. Marca «Mostrar también los inactivos» para verlos todos.",
        "en": "There are no active doctors. Tick “Also show inactive doctors” to see them all.",
    },
    "reactivar_doctor": {"es": "Reactivar doctor", "en": "Reactivate doctor"},
    "reactivar_doctor_ayuda": {
        "es": "El doctor vuelve a aparecer al agendar citas.",
        "en": "The doctor appears again when booking appointments.",
    },
    "boton_reactivar": {"es": "Reactivar", "en": "Reactivate"},

    # ---------- Citas ----------
    "citas_titulo": {"es": "📅 Citas", "en": "📅 Appointments"},
    "tab_agendar": {"es": "Agendar cita", "en": "Book appointment"},
    "tab_gestionar_citas": {"es": "Gestionar citas", "en": "Manage appointments"},
    "aviso_falta_paciente_doctor": {
        "es": "Primero registra al menos un paciente y un doctor activo.",
        "en": "First register at least one patient and one active doctor.",
    },
    "sin_telefono": {"es": "sin tel.", "en": "no phone"},
    "campo_fecha": {"es": "Fecha", "en": "Date"},
    "campo_hora": {"es": "Hora", "en": "Time"},
    "campo_duracion": {"es": "Duración (minutos)", "en": "Duration (minutes)"},
    "campo_motivo": {"es": "Motivo de la consulta", "en": "Reason for the visit"},
    "boton_agendar": {"es": "Agendar", "en": "Book"},
    "cita_agendada": {
        "es": "Cita agendada: {paciente} con {doctor}, {fecha} a las {hora}.",
        "en": "Appointment booked: {paciente} with {doctor}, {fecha} at {hora}.",
    },
    "campo_desde": {"es": "Desde", "en": "From"},
    "campo_hasta": {"es": "Hasta", "en": "To"},
    "sin_citas_rango": {"es": "No hay citas en ese rango.", "en": "No appointments in that range."},
    "opcion_cita": {
        "es": "#{id} · {fecha} {hora} · {paciente} con {doctor} [{estado}]",
        "en": "#{id} · {fecha} {hora} · {paciente} with {doctor} [{estado}]",
    },
    "selecciona_cita": {"es": "Selecciona una cita", "en": "Select an appointment"},
    "cambiar_estado": {"es": "Cambiar estado", "en": "Change status"},
    "campo_estado": {"es": "Estado", "en": "Status"},
    "boton_actualizar_estado": {"es": "Actualizar estado", "en": "Update status"},
    "reprogramar": {"es": "Reprogramar", "en": "Reschedule"},
    "campo_nueva_fecha": {"es": "Nueva fecha", "en": "New date"},
    "campo_nueva_hora": {"es": "Nueva hora", "en": "New time"},

    # ---------- Calendario ----------
    "calendario_titulo": {"es": "🗓️ Calendario y reportes", "en": "🗓️ Calendar and reports"},
    "campo_vista": {"es": "Vista", "en": "View"},
    "vista_dia": {"es": "Día", "en": "Day"},
    "vista_semana": {"es": "Semana", "en": "Week"},
    "todos": {"es": "Todos", "en": "All"},
    "rango_fechas": {"es": "Del {desde} al {hasta}", "en": "From {desde} to {hasta}"},
    "sin_citas_periodo": {"es": "No hay citas en este periodo.", "en": "No appointments in this period."},
    "encabezado_dia": {
        "es": "**{dia} {fecha}** — {cantidad} cita(s)",
        "en": "**{dia} {fecha}** — {cantidad} appointment(s)",
    },
    "estadisticas_periodo": {"es": "Estadísticas del periodo", "en": "Statistics for the period"},
    "sin_datos": {"es": "Sin datos para mostrar.", "en": "No data to show."},

    # ---------- Mi cuenta ----------
    "cuenta_titulo": {"es": "🔑 Mi cuenta", "en": "🔑 My account"},
    "cuenta_usuario": {"es": "Usuario: **{usuario}**", "en": "Username: **{usuario}**"},
    "cambiar_contrasena": {"es": "Cambiar contraseña", "en": "Change password"},
    "campo_contrasena_actual": {"es": "Contraseña actual", "en": "Current password"},
    "campo_contrasena_nueva": {"es": "Contraseña nueva", "en": "New password"},
    "campo_repetir_nueva": {"es": "Repite la contraseña nueva", "en": "Repeat the new password"},
    "error_nuevas_no_coinciden": {
        "es": "Las contraseñas nuevas no coinciden.",
        "en": "The new passwords do not match.",
    },
    "contrasena_cambiada": {
        "es": "Contraseña cambiada. Úsala la próxima vez que inicies sesión.",
        "en": "Password changed. Use it the next time you log in.",
    },

    # ---------- Usuarios ----------
    "usuarios_titulo": {"es": "👥 Usuarios", "en": "👥 Users"},
    "solo_admin": {
        "es": "Solo el administrador puede gestionar usuarios.",
        "en": "Only the administrator can manage users.",
    },
    "tab_nuevo_usuario": {"es": "Nuevo usuario", "en": "New user"},
    "tab_gestionar_usuarios": {"es": "Gestionar usuarios", "en": "Manage users"},
    "campo_rol": {"es": "Rol", "en": "Role"},
    "ayuda_rol": {
        "es": "El personal usa toda la app excepto esta página. El administrador puede gestionar usuarios.",
        "en": "Staff can use the whole app except this page. The administrator can manage users.",
    },
    "campo_contrasena_inicial": {"es": "Contraseña inicial", "en": "Initial password"},
    "ayuda_contrasena_inicial": {
        "es": "Mínimo {minimo} caracteres. La persona puede cambiarla después en «Mi cuenta».",
        "en": "At least {minimo} characters. The person can change it later in “My account”.",
    },
    "boton_crear_usuario": {"es": "Crear usuario", "en": "Create user"},
    "usuario_creado": {
        "es": "Usuario «{usuario}» creado como {rol}.",
        "en": "User “{usuario}” created as {rol}.",
    },
    "sin_otros_usuarios": {"es": "Todavía no hay otros usuarios.", "en": "There are no other users yet."},
    "opcion_usuario": {"es": "{usuario} ({rol}, {estado})", "en": "{usuario} ({rol}, {estado})"},
    "usuario_activo": {"es": "activo", "en": "active"},
    "usuario_inactivo": {"es": "inactivo", "en": "inactive"},
    "selecciona_usuario": {"es": "Selecciona un usuario", "en": "Select a user"},
    "acceso": {"es": "Acceso", "en": "Access"},
    "desactivar_usuario_ayuda": {
        "es": "Un usuario desactivado no puede iniciar sesión, y si la tiene abierta se le cierra.",
        "en": "A deactivated user cannot log in, and an open session is closed.",
    },
    "boton_desactivar_usuario": {"es": "Desactivar usuario", "en": "Deactivate user"},
    "boton_reactivar_usuario": {"es": "Reactivar usuario", "en": "Reactivate user"},
    "restablecer_titulo": {"es": "Restablecer contraseña", "en": "Reset password"},
    "restablecer_ayuda": {
        "es": "Para cuando alguien del personal olvida su contraseña.",
        "en": "For when a staff member forgets their password.",
    },
    "boton_restablecer": {"es": "Restablecer", "en": "Reset"},
    "contrasena_restablecida": {
        "es": "Contraseña de «{usuario}» restablecida.",
        "en": "Password for “{usuario}” has been reset.",
    },

    # ---------- Reiniciar datos ----------
    "reiniciar_titulo": {"es": "⚠️ Reiniciar datos", "en": "⚠️ Reset data"},
    "reiniciar_explicacion": {
        "es": "Borra todos los doctores, pacientes y citas para empezar de cero. "
              "Las cuentas de usuario se conservan.",
        "en": "Deletes all doctors, patients and appointments to start from scratch. "
              "User accounts are kept.",
    },
    "sin_datos_que_borrar": {
        "es": "No hay doctores, pacientes ni citas: los datos ya están en cero.",
        "en": "There are no doctors, patients or appointments: the data is already empty.",
    },
    "reiniciar_advertencia": {
        "es": "Esta acción no se puede deshacer desde la app. Antes de borrar, "
              "se guarda una copia de seguridad en la carpeta respaldos/.",
        "en": "This cannot be undone from the app. Before deleting, "
              "a backup copy is saved in the respaldos/ folder.",
    },
    "reiniciar_entiendo": {
        "es": "Entiendo que se borrarán todos los doctores, pacientes y citas.",
        "en": "I understand that all doctors, patients and appointments will be deleted.",
    },
    "palabra_confirmar": {"es": "BORRAR", "en": "DELETE"},
    "reiniciar_escribe": {"es": "Escribe {palabra} para confirmar", "en": "Type {palabra} to confirm"},
    "boton_reiniciar": {"es": "Borrar todo y empezar de cero", "en": "Delete everything and start over"},
    # Modo demostración (demo.py)
    "demo_aviso": {
        "es": "🧪 Demostración: los datos son de ejemplo y los comparten todas las visitas. "
              "No escribas datos reales.",
        "en": "🧪 Demo: the data is sample data shared by all visitors. Don't enter real data.",
    },
    "demo_acceso": {
        "es": "🧪 Esto es una demostración. Entra con el usuario **{usuario}** y la contraseña **{contrasena}**.",
        "en": "🧪 This is a demo. Sign in with username **{usuario}** and password **{contrasena}**.",
    },
    "reinicio_hecho": {
        "es": "Datos borrados: {doctores} doctores, {pacientes} pacientes y {citas} citas. "
              "Copia de seguridad guardada en {respaldo}.",
        "en": "Data deleted: {doctores} doctors, {pacientes} patients and {citas} appointments. "
              "Backup saved in {respaldo}.",
    },

    # ---------- Errores de validación (los lanza database.py) ----------
    "err_contrasena_corta": {
        "es": "La contraseña debe tener al menos {minimo} caracteres.",
        "en": "The password must have at least {minimo} characters.",
    },
    "err_usuario_obligatorio": {"es": "El usuario es obligatorio.", "en": "The username is required."},
    "err_rol_invalido": {"es": "Rol no válido: {rol}", "en": "Invalid role: {rol}"},
    "err_usuario_existe": {"es": "Ese usuario ya existe.", "en": "That username already exists."},
    "err_contrasena_actual": {
        "es": "La contraseña actual no es correcta.",
        "en": "The current password is incorrect.",
    },
    "err_contrasena_igual": {
        "es": "La contraseña nueva debe ser distinta de la actual.",
        "en": "The new password must be different from the current one.",
    },
    "err_ultimo_admin": {
        "es": "Debe quedar al menos un administrador activo.",
        "en": "At least one active administrator must remain.",
    },
    "err_nombre_apellido": {
        "es": "El nombre y el apellido son obligatorios.",
        "en": "First name and last name are required.",
    },
    "err_nombre_especialidad": {
        "es": "El nombre y la especialidad son obligatorios.",
        "en": "Name and specialty are required.",
    },
    "err_fecha_pasada": {
        "es": "No se puede agendar una cita en una fecha pasada.",
        "en": "An appointment cannot be booked on a past date.",
    },
    "err_choque_horario": {
        "es": "El doctor ya tiene una cita en ese horario.",
        "en": "The doctor already has an appointment at that time.",
    },
    "err_cita_no_existe": {"es": "La cita no existe.", "en": "The appointment does not exist."},
    "err_estado_invalido": {"es": "Estado no válido: {estado}", "en": "Invalid status: {estado}"},
}


def traducir(clave, idioma=IDIOMA_POR_DEFECTO, **valores):
    """Devuelve el texto de la clave en el idioma pedido, rellenando los {valores}."""
    texto = TEXTOS[clave][idioma]
    return texto.format(**valores) if valores else texto


class ErrorValidacion(ValueError):
    """Error con una clave de traducción, para mostrarlo en el idioma elegido.

    str(error) da el texto en español, así que se puede usar como un ValueError normal.
    """

    def __init__(self, clave, **valores):
        self.clave = clave
        self.valores = valores
        super().__init__(traducir(clave, "es", **valores))


# ---------- Funciones para las páginas de Streamlit ----------

def idioma_actual():
    import streamlit as st  # aquí dentro para que database.py no dependa de Streamlit

    return st.session_state.get("idioma", IDIOMA_POR_DEFECTO)


def t(clave, **valores):
    """Texto de la clave en el idioma elegido en la barra lateral."""
    return traducir(clave, idioma_actual(), **valores)


def t_error(error):
    """Mensaje de un error en el idioma elegido."""
    if isinstance(error, ErrorValidacion):
        return t(error.clave, **error.valores)
    return str(error)


def formato_opcion(prefijo):
    """format_func para selectores cuyas opciones son valores guardados (p. ej. estados).

    Fija el idioma al crear el selector, así la traducción no depende de cuándo se llame.
    """
    idioma = idioma_actual()
    return lambda valor: traducir(f"{prefijo}{valor}", idioma)


def formatear_fecha(fecha):
    """Fecha corta según el idioma: 21/10/2026 o 10/21/2026."""
    return fecha.strftime(t("strftime_fecha"))


def preparar_tabla(tabla):
    """Copia la tabla con los valores guardados traducidos y las columnas renombradas."""
    tabla = tabla.copy()
    if "estado" in tabla.columns:
        tabla["estado"] = tabla["estado"].map(lambda estado: t(f"estado_{estado}"))
    if "rol" in tabla.columns:
        tabla["rol"] = tabla["rol"].map(lambda rol: t(f"rol_{rol}"))
    if "activo" in tabla.columns:
        tabla["activo"] = tabla["activo"].map(lambda activo: t("si") if activo else t("no"))
    nombres = {col: t(f"col_{col}") for col in tabla.columns if f"col_{col}" in TEXTOS}
    return tabla.rename(columns=nombres)
