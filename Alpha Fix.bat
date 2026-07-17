@echo off
cd /d "%~dp0"
echo Starting Alpha Fix Production...
uv run python -m alpha_fix --gui
