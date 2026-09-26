@echo off
setlocal

cd /d "%~dp0"
set "APP_RELEASE_TAG=local"

where uv >nul 2>nul
if errorlevel 1 (
    echo [ERROR] uv was not found. Install it from https://docs.astral.sh/uv/
    pause
    exit /b 1
)

echo Building SultansGameEventViewer_local.exe...
uv run --python 3.11 --with pyinstaller python -m PyInstaller --clean --noconfirm --distpath "." --workpath ".\.build" ".\event_viewer.spec"
if errorlevel 1 (
    echo.
    echo [ERROR] Build failed.
    pause
    exit /b 1
)

if not exist "SultansGameEventViewer_local.exe" (
    echo.
    echo [ERROR] Build finished but the executable was not found.
    pause
    exit /b 1
)

echo.
echo [OK] Created: %CD%\SultansGameEventViewer_local.exe
pause
