@echo off
:: Instalador completo - Analisis de Combinaciones
:: Instala Python, pip y dependencias automaticamente
:: Ejecutar como Administrador si necesita instalar Python

cd /d "%~dp0"
title Instalador - Analisis de Combinaciones

echo ============================================
echo   INSTALADOR - Analisis de Combinaciones
echo ============================================
echo.

:: -----------------------------------------------
:: 1. Verificar si Python esta instalado
:: -----------------------------------------------
echo [1/5] Verificando Python...

where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i
    echo       Python encontrado: %PYTHON_VER%
    set PYTHON_CMD=python
    goto :CHECK_PIP
)

where python3 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    for /f "tokens=*" %%i in ('python3 --version 2^>^&1') do set PYTHON_VER=%%i
    echo       Python encontrado: %PYTHON_VER%
    set PYTHON_CMD=python3
    goto :CHECK_PIP
)

:: Python no encontrado - intentar instalar
echo       Python NO encontrado. Intentando instalar...
echo.

:: Verificar si winget esta disponible
where winget >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo       Instalando Python via winget...
    winget install Python.Python.3.11 --accept-package-agreements --accept-source-agreements
    if %ERRORLEVEL% EQU 0 (
        echo       Python instalado correctamente.
        echo       IMPORTANTE: Cierra y vuelve a abrir este .bat para que el PATH se actualice.
        echo.
        
        :: Refrescar PATH para la sesion actual
        for /f "tokens=2*" %%A in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul') do set "SYS_PATH=%%B"
        for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "USR_PATH=%%B"
        set "PATH=%SYS_PATH%;%USR_PATH%"
        
        where python >nul 2>&1
        if %ERRORLEVEL% EQU 0 (
            set PYTHON_CMD=python
            goto :CHECK_PIP
        )
        
        echo       No se pudo detectar Python tras la instalacion.
        echo       Por favor, cierra esta ventana, abre una nueva y ejecuta este .bat de nuevo.
        pause
        exit /b 1
    ) else (
        echo       ERROR: No se pudo instalar Python con winget.
        goto :MANUAL_PYTHON
    )
) else (
    goto :MANUAL_PYTHON
)

:MANUAL_PYTHON
echo.
echo ============================================
echo   PYTHON NO ENCONTRADO
echo ============================================
echo.
echo   No se pudo instalar Python automaticamente.
echo   Por favor, instala Python manualmente:
echo.
echo   1. Ve a https://www.python.org/downloads/
echo   2. Descarga Python 3.11 o superior
echo   3. IMPORTANTE: Marca "Add Python to PATH" durante la instalacion
echo   4. Ejecuta este .bat de nuevo
echo.
echo ============================================
pause
exit /b 1

:: -----------------------------------------------
:: 2. Verificar pip
:: -----------------------------------------------
:CHECK_PIP
echo [2/5] Verificando pip...

%PYTHON_CMD% -m pip --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo       pip disponible.
) else (
    echo       pip NO encontrado. Instalando...
    %PYTHON_CMD% -m ensurepip --upgrade >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo       ensurepip fallo. Descargando get-pip.py...
        powershell -Command "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'get-pip.py'"
        %PYTHON_CMD% get-pip.py
        del get-pip.py >nul 2>&1
    )
    %PYTHON_CMD% -m pip --version >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo       ERROR: No se pudo instalar pip.
        pause
        exit /b 1
    )
    echo       pip instalado correctamente.
)

:: -----------------------------------------------
:: 3. Crear entorno virtual
:: -----------------------------------------------
:CREATE_VENV
echo [3/5] Configurando entorno virtual...

if exist ".venv\Scripts\python.exe" (
    echo       Entorno virtual ya existe.
) else (
    echo       Creando entorno virtual...
    %PYTHON_CMD% -m venv .venv
    if %ERRORLEVEL% NEQ 0 (
        echo       ERROR: No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
    echo       Entorno virtual creado.
)

:: -----------------------------------------------
:: 4. Actualizar pip en el entorno virtual
:: -----------------------------------------------
echo [4/5] Actualizando pip del entorno virtual...
.venv\Scripts\python.exe -m pip install --upgrade pip >nul 2>&1
echo       pip actualizado.

:: -----------------------------------------------
:: 5. Instalar dependencias
:: -----------------------------------------------
echo [5/5] Instalando dependencias (esto puede tardar unos minutos)...
echo.

.venv\Scripts\python.exe -m pip install -r requirements.txt

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================
    echo   INSTALACION COMPLETADA CON EXITO
    echo ============================================
    echo.
    echo   Todo esta listo. Ejecuta "Ejecutar.bat"
    echo   para iniciar la aplicacion.
    echo.
    echo ============================================
) else (
    echo.
    echo ============================================
    echo   ERROR EN LA INSTALACION
    echo ============================================
    echo.
    echo   Hubo errores al instalar las dependencias.
    echo   Revisa los mensajes anteriores.
    echo.
    echo ============================================
)

echo.
pause
