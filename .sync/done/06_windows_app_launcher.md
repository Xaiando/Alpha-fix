# Windows App Launcher

**Claim:** `verified`
**Scope:** `graduate_to_alpha_fix`
**Component:** launchers, shortcuts, root app entry flow

**Context:**
The user wants Alpha Fix to behave like a usable desktop app again: double-click an icon and the GUI opens, without needing to type commands in a terminal.

**Task:**
1. make production and sandbox launchable from the folder by double-click
2. avoid depending on `uv` for normal app startup
3. create icon-based Windows shortcuts for both apps
4. keep CLI access intact for debugging and batch work

---

## Completion Summary

- Replaced the old `uv`-based production batch launcher with a local `.venv` launcher.
- Added matching sandbox launcher batch file.
- Added hidden GUI launchers:
  - `Alpha Fix.vbs`
  - `Alpha Fix Sandbox.vbs`
- Added shortcut installer:
  - `Install Shortcuts.ps1`
- Created icon-based Windows shortcuts in the app root:
  - `Alpha Fix.lnk`
  - `Alpha Fix Sandbox.lnk`

## Verification

- `& '.\Alpha Fix.bat' --help`
- `& '.\Alpha Fix Sandbox.bat' --help`
- `powershell -ExecutionPolicy Bypass -File '.\Install Shortcuts.ps1'`
- Shortcut integrity check:
  - `Alpha Fix.lnk` targets `C:\Windows\System32\wscript.exe` with `Alpha Fix.vbs`
  - `Alpha Fix Sandbox.lnk` targets `C:\Windows\System32\wscript.exe` with `Alpha Fix Sandbox.vbs`

## Parallel Split

- Codex stays on main app / production usability and workflow.
- Antigravity stays on sandbox experiments and exploratory math.
