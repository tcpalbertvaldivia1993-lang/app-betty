#!/usr/bin/env bash
# Copia de seguridad automática de las clínicas de la nube.
# La lanza cada semana el Programador de tareas de Windows (ver README):
#   wsl.exe -d Ubuntu -- bash /home/administrator/app-betty/copia_automatica.sh
# Necesita la dirección de Neon en .streamlit/secrets.toml.
# Lo que pasa en cada copia se anota en respaldos_nube/registro.txt.

cd "$(dirname "$0")" || exit 1
mkdir -p respaldos_nube
.venv/bin/python respaldar_nube.py --sin-preguntar >> respaldos_nube/registro.txt 2>&1
