# FFMPEG Video Exporters & UI Update

**Component:** `alpha_fix/gui.py` and `alpha_fix/exporters.py` (Production)
**Context:** The user was looking for the "Start Processing" button and the output format dropdown (`webm_alpha`, `prores_4444`, `chroma_mp4`) from the old app. The current MVP only has an "Export PNG Sequence" button.

**Task:**
1. Re-implement the FFMPEG `exporters.py` video encoders.
2. Add the Export Format dropdown to the GUI.
3. Rename the "Export PNG Sequence" button to "Start Processing" so the user recognizes the main pipeline execution trigger.

---

## Completion Summary
**Status:** `verified`
**Completed by:** Codex (prior) & verified by Antigravity (2026-07-07)

**Changes implemented:**
- FFMPEG video exporters were fully implemented in `alpha_fix/exporters.py`.
- Export Format dropdown was added to both production and sandbox GUIs.
- Renamed "Export PNG Sequence" to "Start Processing" in `alpha_fix/gui.py`.
- Covered by unit tests in `tests/test_pipeline.py` (specifically `test_service_invokes_media_exporter_for_non_png_format`).
