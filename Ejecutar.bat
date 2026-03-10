@echo off
:: Iniciar Análisis de Combinaciones - Lotería IA
:: Doble clic para ejecutar

cd /d "%~dp0"

:: Verificar si existe el entorno virtual
if exist ".venv\Scripts\python.exe" (
    set PYTHON=.venv\Scripts\python.exe
) else (
    set PYTHON=python
)

:: Suprimir warnings de TensorFlow
set TF_CPP_MIN_LOG_LEVEL=3
set TF_ENABLE_ONEDNN_OPTS=0

echo Iniciando Analisis de Combinaciones - Loteria IA...
"%PYTHON%" main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR al ejecutar la aplicacion.
    echo Intenta instalar dependencias: pip install -r requirements.txt
    pause
)
