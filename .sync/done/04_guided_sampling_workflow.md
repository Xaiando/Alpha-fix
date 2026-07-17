# Guided Sampling Workflow

**Claim:** `verified`
**Scope:** `graduate_to_alpha_fix`
**Component:** `alpha_fix/gui.py`, `alpha_fix/service.py`

**Context:**
Historical screenshots show the old working app used operator-guided ellipse and rectangle samples. The current rebuilt production app still relies on border-driven inference only, which is not enough for difficult overlays or white-on-white subject extraction.

**Task:**
Rebuild a first-frame guided sampling workflow for production:
1. Let the operator place ellipse or rectangle sample regions.
2. Distinguish between background-style and keep-style samples.
3. Persist presets so the same layout can be reused across clips.

**Why it matters:**
This moves `alpha_fix` back toward the original app's real workflow instead of leaving the operator with only raw parameter tuning.

---

## Completion Summary

- Added `SampleRegion` support with JSON preset save/load in `alpha_fix/samples.py`.
- Hooked background and keep regions into the production pipeline:
  - background regions contribute background palette pixels and directly suppress alpha
  - keep regions directly reinforce alpha
- Added a production sample editor dialog in `alpha_fix/sample_editor.py`.
- Added GUI actions for edit, load, save, and clear in `alpha_fix/gui.py`.
- Added CLI preset support with `--sample-preset` in `alpha_fix/cli.py`.
- Added tests for sample overrides and preset round-tripping in `tests/test_pipeline.py`.

## Verification

- `uv run python -m unittest discover -s tests -v`
- `uv run alpha-fix --help`
- `uv run python -m compileall alpha_fix alpha_fix_2`
- Real still-image smoke test:
  - asset: `Overlay\\Hailuo_Image_Make me a stream overlay conta_494485647038263305.jpg`
  - without guided sample preset: `center_mean_alpha = 0.7168`
  - with one central background sample preset: `center_mean_alpha = 0.0000`

## Follow-Up

- The next production improvement should be richer sample semantics and preset management, not more raw slider growth.
