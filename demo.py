"""Modo demostración, para publicar la app en internet (por ejemplo en Streamlit Community Cloud).

Se activa con la variable de entorno MODO_DEMO=1. En Streamlit Community Cloud se pone en
"Advanced settings → Secrets" como:  MODO_DEMO = "1"

En modo demostración:
- Se crea solo un usuario administrador con usuario y contraseña públicos, que se muestran en
  la pantalla de acceso. Así nadie puede adueñarse de la app creando el primer administrador.
- Si no hay doctores ni pacientes, se cargan los datos de ejemplo (también después de reiniciar).
- Se ocultan "Mi cuenta" y "Usuarios", para que ningún visitante cambie la contraseña de la
  demostración y deje fuera a los demás.

Sin MODO_DEMO, la app funciona como siempre (instalación en la clínica).
"""

import os
import threading

import database as bd
import datos_ejemplo

ACTIVO = os.environ.get("MODO_DEMO") == "1"
USUARIO = "demo"
CONTRASENA = "demo1234"

# Todas las visitas comparten el mismo proceso: el candado evita que dos visitas
# carguen los datos de ejemplo a la vez y queden duplicados.
_candado = threading.Lock()


def preparar():
    """Crea el usuario de demostración y los datos de ejemplo si faltan."""
    with _candado:
        if not bd.hay_usuarios():
            bd.crear_usuario(USUARIO, CONTRASENA, rol="administrador")
        datos_ejemplo.cargar()
