@echo off
setlocal
cd /d "%~dp0"
where uv >nul 2>nul
if errorlevel 1 (
  echo Please install uv from https://docs.astral.sh/uv/getting-started/installation/
  pause
  exit /b 1
)
uv sync --locked
if errorlevel 1 (
  echo Setup failed. See the error above.
  pause
  exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\Create Shortcut.ps1"
echo Alpha Fix is ready. Open Alpha Fix.lnk or Alpha Fix.vbs to launch.
pause
