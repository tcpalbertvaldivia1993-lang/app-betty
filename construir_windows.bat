@echo off
rem Construye ClinicaCitas.exe y el ZIP para instalar en la clinica.
rem Se ejecuta en Windows, con Python 3 instalado:  construir_windows.bat
rem Resultado: dist\ClinicaCitas-windows.zip

setlocal
cd /d "%~dp0"

echo === 1/4 Entorno de Python para Windows (.venv-win) ===
if not exist .venv-win\Scripts\python.exe (
    py -3 -m venv .venv-win || goto :error
)
.venv-win\Scripts\python -m pip install --quiet --upgrade pip || goto :error
.venv-win\Scripts\python -m pip install --quiet -r requirements.txt -r requirements-dev.txt || goto :error

echo === 2/4 Pruebas ===
.venv-win\Scripts\python -m pytest -q || goto :error

echo === 3/4 Empaquetando con PyInstaller ===
.venv-win\Scripts\python -m PyInstaller --noconfirm --clean --onedir --name ClinicaCitas ^
    --collect-all streamlit --copy-metadata streamlit ^
    --add-data "app.py;." --add-data "database.py;." --add-data "traducciones.py;." ^
    --add-data "demo.py;." --add-data "datos_ejemplo.py;." --add-data "paginas;paginas" ^
    lanzador.py || goto :error

echo === 4/4 Comprimiendo en ZIP ===
copy /y INSTALACION_CLINICA.md dist\ClinicaCitas\ >nul || goto :error
powershell -NoProfile -Command "Compress-Archive -Path 'dist\ClinicaCitas' -DestinationPath 'dist\ClinicaCitas-windows.zip' -Force" || goto :error

echo.
echo Listo: dist\ClinicaCitas-windows.zip
exit /b 0

:error
echo.
echo ERROR: la construccion fallo. Revisa los mensajes de arriba.
exit /b 1
