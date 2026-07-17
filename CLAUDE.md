# Alpha Fix

Video alpha-matte cleanup tool. Two pipelines: `alpha_fix/` (SUBJECT mode: LIPC halo suppression; OVERLAY mode: CHHC hole carving) and `alpha_fix_2/` (sandbox/experimental). Python via `uv` (`uv sync`, tests in `tests/`). GUIs in each package's `gui.py`.

## Coordination

Multi-agent project (Claude, Codex, Antigravity). Protocol: `coordination/TEAM_PROTOCOL.md`. Check `coordination/STATUS_BOARD.md` before starting work; log decisions in `coordination/DECISIONS.md`.

Claude's check-in journal (history, proposals, audit findings): `coordination/claude-journal.md` — read it when context on past decisions is needed, do not load it by default. Append new check-ins there, never to this file.
