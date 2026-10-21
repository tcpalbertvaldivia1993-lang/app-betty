"""Punto de entrada del programa para Windows (ClinicaCitas.exe).

Arranca el servidor de la app, abre el navegador y muestra la dirección
que deben usar las otras computadoras de la clínica.

También se puede probar sin empaquetar:  python lanzador.py
"""

import os
import socket
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

PUERTO = 8501
URL_LOCAL = f"http://localhost:{PUERTO}"


def carpeta_del_programa():
    """Carpeta donde está ClinicaCitas.exe (o este script, si se ejecuta con Python)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def carpeta_de_la_app():
    """Carpeta donde están app.py y paginas/ (dentro del paquete cuando es .exe)."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent


def puerto_en_uso():
    """True si ya hay algo escuchando en el puerto (la app ya está abierta)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as conexion:
        conexion.settimeout(1)
        return conexion.connect_ex(("127.0.0.1", PUERTO)) == 0


def ip_de_esta_pc():
    """IP de esta computadora en la red local (la que usan las otras PCs)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as conexion:
            # No envía nada: solo pregunta qué interfaz se usaría para salir a la red
            conexion.connect(("8.8.8.8", 80))
            return conexion.getsockname()[0]
    except OSError:
        return socket.gethostbyname(socket.gethostname())


def abrir_navegador_cuando_este_lista():
    """Espera a que el servidor responda y abre la app en el navegador."""
    for _ in range(120):  # hasta 60 segundos
        try:
            with urllib.request.urlopen(f"{URL_LOCAL}/_stcore/health", timeout=1):
                webbrowser.open(URL_LOCAL)
                return
        except OSError:
            time.sleep(0.5)
    print("El servidor tarda en arrancar. Abre a mano:", URL_LOCAL)


def main():
    # Si la consola de Windows no puede mostrar algún carácter, que lo reemplace en vez de fallar
    sys.stdout.reconfigure(errors="replace")

    if puerto_en_uso():
        print("La app ya está abierta. Abriendo el navegador...")
        webbrowser.open(URL_LOCAL)
        time.sleep(2)
        return

    # Los datos se guardan junto al programa, en la carpeta datos\ (los respaldos, en datos\respaldos\)
    carpeta_datos = carpeta_del_programa() / "datos"
    carpeta_datos.mkdir(exist_ok=True)
    os.environ["CLINICA_BD"] = str(carpeta_datos / "clinica.db")

    print("=" * 60)
    print("  Clínica - Citas")
    print("=" * 60)
    print("  NO CIERRES ESTA VENTANA: si la cierras, la app se detiene.")
    print()
    print(f"  En esta computadora:      {URL_LOCAL}")
    print(f"  En las otras PCs y móviles: http://{ip_de_esta_pc()}:{PUERTO}")
    print(f"  Datos guardados en:       {carpeta_datos}")
    print("=" * 60)

    threading.Thread(target=abrir_navegador_cuando_este_lista, daemon=True).start()

    from streamlit.web import cli as stcli  # aquí dentro: tarda en cargar

    sys.argv = [
        "streamlit", "run", str(carpeta_de_la_app() / "app.py"),
        "--server.address=0.0.0.0",  # escucha también a las otras PCs de la red
        f"--server.port={PUERTO}",
        "--server.headless=true",  # el navegador lo abrimos nosotros
        "--server.fileWatcherType=none",  # el código no cambia mientras corre
        "--global.developmentMode=false",
        "--browser.gatherUsageStats=false",  # no enviar estadísticas de uso fuera de la clínica
    ]
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
