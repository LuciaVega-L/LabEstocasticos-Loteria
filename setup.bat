@echo off
chcp 65001 >nul
title Predictor de Lotería — Cadenas de Markov

echo.
echo  ================================================
echo   Predictor de Lotería — Cadenas de Markov
echo  ================================================
echo.

:: ── Verificar que Python esté instalado ─────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python no encontrado. Instálalo desde https://python.org
    pause
    exit /b 1
)

:: ── Crear entorno virtual si no existe ──────────────────────────────────────
if not exist ".venv" (
    echo  [1/3] Creando entorno virtual...
    python -m venv .venv
    if errorlevel 1 (
        echo  [ERROR] No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
    echo        Entorno virtual creado.
) else (
    echo  [1/3] Entorno virtual ya existe, omitiendo creacion.
)

:: ── Instalar dependencias si no están ───────────────────────────────────────
echo  [2/3] Verificando dependencias...
.venv\Scripts\python.exe -c "import PyQt6" >nul 2>&1
if errorlevel 1 (
    echo        Instalando PyQt6...
    .venv\Scripts\pip.exe install PyQt6 PyQt6-tools --quiet
    if errorlevel 1 (
        echo  [ERROR] No se pudieron instalar las dependencias.
        pause
        exit /b 1
    )
)

.venv\Scripts\python.exe -c "import pandas" >nul 2>&1
if errorlevel 1 (
    echo        Instalando pandas y openpyxl...
    .venv\Scripts\pip.exe install pandas openpyxl --quiet
)

.venv\Scripts\python.exe -c "import scipy" >nul 2>&1
if errorlevel 1 (
    echo        Instalando scipy...
    .venv\Scripts\pip.exe install scipy --quiet
)

echo        Dependencias listas.

:: ── Ejecutar la aplicación ───────────────────────────────────────────────────
echo  [3/3] Iniciando aplicacion...
echo.
.venv\Scripts\python.exe Flujo\main_app.py

if errorlevel 1 (
    echo.
    echo  [ERROR] La aplicacion cerro con un error.
    pause
)
