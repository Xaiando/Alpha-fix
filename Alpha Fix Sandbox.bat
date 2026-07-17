@echo off
cd /d "%~dp0"
echo Starting Alpha Fix Sandbox...
uv run python -m alpha_fix_2 --gui
