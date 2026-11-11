@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

echo ==================================================
echo   Arab Templates - starting swarm + dashboard
echo ==================================================

rem The Windows Store "python.exe" alias exits immediately after launching, which
rem breaks background process tracking, so resolve the real interpreter first.
set "PY="
for /f "delims=" %%p in ('python -c "import sys; print(sys.executable)" 2^>nul') do set "PY=%%p"
if not defined PY (
  echo [ERROR] Python 3.10+ is required and must be in PATH.
  echo.
  pause
  exit /b 1
)
echo [ok] interpreter: %PY%
echo.

"%PY%" "scripts\start_services.py" --open
if errorlevel 1 (
  echo.
  echo [ERROR] startup failed - see logs\dashboard_console.log
  pause
  exit /b 1
)

echo.
echo Keep this window closed - services run in the background.
timeout /t 5 >nul
exit /b 0
