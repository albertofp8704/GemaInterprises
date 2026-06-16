@echo off
title GEMA - Instalacion Automatica
color 0B
cls

echo.
echo  =============================================
echo     GEMA - Agente Holografico
echo     Instalacion y arranque automatico
echo  =============================================
echo.

:: ── Verificar Git ───────────────────────────────────────────
git --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo  [ERROR] Git no esta instalado.
    echo.
    echo  1. Abre este enlace en tu navegador:
    echo     https://git-scm.com/download/win
    echo  2. Descarga e instala Git
    echo  3. Vuelve a ejecutar este archivo
    echo.
    start https://git-scm.com/download/win
    pause
    exit /b 1
)

:: ── Verificar Node.js ────────────────────────────────────────
node --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo  [ERROR] Node.js no esta instalado.
    echo.
    echo  1. Abre este enlace en tu navegador:
    echo     https://nodejs.org/
    echo  2. Descarga e instala la version LTS
    echo  3. Vuelve a ejecutar este archivo
    echo.
    start https://nodejs.org/
    pause
    exit /b 1
)

echo  [OK] Git y Node.js detectados.
echo.

:: ── Ir al directorio del usuario ─────────────────────────────
cd /d "%USERPROFILE%"

:: ── Clonar o actualizar el repositorio ───────────────────────
if exist "GemaInterprises\electron-agent\" (
    echo  Actualizando GEMA...
    cd GemaInterprises
    git pull
    echo.
) else (
    echo  Descargando GEMA por primera vez...
    git clone https://github.com/albertofp8704/GemaInterprises
    if errorlevel 1 (
        color 0C
        echo.
        echo  [ERROR] No se pudo descargar el repositorio.
        echo  Comprueba tu conexion a Internet.
        pause
        exit /b 1
    )
    cd GemaInterprises
    echo.
)

:: ── Entrar a la carpeta del agente ───────────────────────────
cd electron-agent

:: ── Crear config.json si no existe ──────────────────────────
if not exist "config.json" (
    copy config.json.example config.json >nul
    echo  ============================================
    echo   CONFIGURACION NECESARIA
    echo  ============================================
    echo.
    echo  Se va a abrir el archivo config.json.
    echo  Sustituye  sk-ant-TU_CLAVE_AQUI  por tu
    echo  clave de Anthropic y guarda el archivo.
    echo.
    echo  (Puedes obtener una clave en: anthropic.com)
    echo.
    pause
    notepad config.json
    echo.
    echo  Presiona Enter cuando hayas guardado la clave...
    pause >nul
)

:: ── Instalar dependencias ────────────────────────────────────
echo  Instalando dependencias (primera vez puede tardar 2-3 min)...
call npm install
if errorlevel 1 (
    color 0C
    echo.
    echo  [ERROR] Fallo al instalar dependencias.
    pause
    exit /b 1
)

:: ── Arrancar GEMA ────────────────────────────────────────────
echo.
echo  Iniciando GEMA...
echo  (La ventana holografica aparecera en la esquina inferior derecha)
echo.
call npm start
