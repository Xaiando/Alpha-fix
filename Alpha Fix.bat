@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run Setup.bat first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m alpha_fix --gui
if errorlevel 1 pause
