@echo off
chcp 65001 >nul
title Predictor de Loteria - Cadenas de Markov

echo.
echo  ================================================
echo   Predictor de Loteria - Cadenas de Markov
echo  ================================================
echo.

:: Moverse a la carpeta donde esta este .bat
cd /d "%~dp0"

:: ── Buscar Python disponible en este equipo ──────────────────────────────────
set PYTHON_CMD=

python --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=python
    goto :python_encontrado
)

python3 --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=python3
    goto :python_encontrado
)

for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "C:\Python313\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
    "C:\Python310\python.exe"
    "%ProgramFiles%\Python313\python.exe"
    "%ProgramFiles%\Python312\python.exe"
    "%ProgramFiles%\Python311\python.exe"
) do (
    if exist %%P (
        set PYTHON_CMD=%%P
        goto :python_encontrado
    )
)

echo  [ERROR] No se encontro Python en este equipo.
echo          Descargalo desde https://python.org
echo          Marca "Add Python to PATH" al instalarlo.
echo.
pause
exit /b 1

:python_encontrado
echo  [OK] Python encontrado: %PYTHON_CMD%

:: ── Verificar si el venv existe y es valido para este equipo ────────────────
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe --version >nul 2>&1
    if errorlevel 1 (
        echo  [!] Entorno virtual de otro equipo detectado, recreando...
        rmdir /s /q .venv
    ) else (
        echo  [1/3] Entorno virtual valido encontrado.
        goto :instalar_deps
    )
)

:: ── Crear entorno virtual ────────────────────────────────────────────────────
echo  [1/3] Creando entorno virtual...
%PYTHON_CMD% -m venv .venv
if errorlevel 1 (
    echo  [ERROR] No se pudo crear el entorno virtual.
    pause
    exit /b 1
)
echo        Entorno virtual creado correctamente.

:: ── Instalar dependencias ────────────────────────────────────────────────────
:instalar_deps
echo  [2/3] Verificando dependencias...

set PIP=.venv\Scripts\pip.exe
set PYEXE=.venv\Scripts\python.exe

%PYEXE% -c "import PyQt6" >nul 2>&1
if errorlevel 1 (
    echo        Instalando PyQt6...
    %PIP% install PyQt6 PyQt6-tools --quiet
    if errorlevel 1 (
        echo  [ERROR] No se pudo instalar PyQt6. Verifica tu conexion a internet.
        pause
        exit /b 1
    )
)

%PYEXE% -c "import pandas" >nul 2>&1
if errorlevel 1 (
    echo        Instalando pandas y openpyxl...
    %PIP% install pandas openpyxl --quiet
)

%PYEXE% -c "import scipy" >nul 2>&1
if errorlevel 1 (
    echo        Instalando scipy...
    %PIP% install scipy --quiet
)

echo        Todas las dependencias estan listas.

:: ── Lanzar la aplicacion ─────────────────────────────────────────────────────
echo  [3/3] Iniciando aplicacion...
echo.
%PYEXE% Flujo\main_app.py

if errorlevel 1 (
    echo.
    echo  [ERROR] La aplicacion cerro con un error.
    pause
)
