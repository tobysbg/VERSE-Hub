@echo off
REM ===========================================================================
REM JARVIS launcher for Windows 11.
REM Creates a virtual environment, installs core dependencies, and starts JARVIS.
REM ===========================================================================
setlocal

cd /d "%~dp0"

if not exist ".venv\" (
    echo [JARVIS] Creating virtual environment...
    python -m venv .venv
)

echo [JARVIS] Activating virtual environment...
call ".venv\Scripts\activate.bat"

echo [JARVIS] Installing core dependencies...
python -m pip install --upgrade pip >nul
python -m pip install -r requirements.txt

echo [JARVIS] Starting JARVIS...
REM Run as a module from the repository root (parent of this folder).
cd /d "%~dp0.."
python -m jarvis.app.main

endlocal
