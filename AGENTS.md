# Alpha Fix 3

This is the rewritten project. The original app is at `E:\Temp\Projects\Tools\Alpha Fix` and is reference material, not an edit target.

- Use Python 3.12+ through `uv`. Run `uv sync --locked` to prepare the environment.
- `src/alpha_fix/engines/operator.py` preserves the known-good original `alpha_fix_2` processor. Research lives separately in `engines/research.py`; neither processor inherits from the other.
- Shared numerical primitives are in `engines/primitives.py`. Preserve algorithm behavior unless the user asks to change it. `docs/source-provenance.json` records the original source hashes.
- `project.py`, `media.py`, and `service.py` must remain independent of Qt. Desktop widgets belong in `ui/`.
- Each media file owns its own settings and normalized sample regions. Preserve compatibility with legacy sample JSON.
- Every export uses a fresh staging directory and publishes a unique completed run. Never delete or reuse the user's output directory or source files.
- Process previews through the same sequential state as exports. Keep worker-thread operations away from Qt widgets; cancellation uses an event and cleanup happens before thread disposal.
- Check changes using `uv run pytest -q` and `uv run python -m compileall -q src`. For engine changes, run `uv run python tools/verify_parity.py "E:\Temp\Projects\Tools\Alpha Fix"` and explain any intentional differences.
- `uv run python tools/render_workspace.py` renders the app's own widgets and updates the synthetic demo. Review PNGs under `docs/screenshots` after interface changes.
