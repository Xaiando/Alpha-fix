# App Improvements

Last updated: 2026-05-13 15:45:00 +02:00

## Now

1. Sandbox overlay seed ranking
   Scope: `sandbox_only_alpha_fix_2`
   Why: `auto_hole` now finds seeds, but the real asset failure is wrong seed choice, not missing seeds.
   Candidate directions: centrality scoring, rectangle-likeness, paired-window symmetry, reject edge-connected mega-components.

2. Sandbox outer-frame model
   Scope: `sandbox_only_alpha_fix_2`
   Why: `frame_fill` grows to almost the full frame on the tested overlay still, which poisons flood fill.
   Candidate directions: better outer contour selection, border-connected suppression, frame-band confidence gating.

3. Production guided sampling workflow
   Scope: `graduate_to_alpha_fix`
   Why: historical screenshots show sample placement was part of the working app; border-only inference is not enough.
   Candidate directions: ellipse/rect sample regions, first-frame operator placement, reusable presets.

## Next

1. Metrics and review surface
   Scope: both
   Why: experimental branches need the same evidence format every time.
   Add: center-hole score, frame-band opacity score, export-write error coverage, temporal diagnostics.

2. Sandbox math ablation discipline
   Scope: `sandbox_only_alpha_fix_2`
   Why: `SDR-Pow` and `OSA-v2` exist, but neither is yet justified by measured improvement on real assets.
   Add: fixed pass table, asset set, and promotion thresholds.

3. Production exporter polish
   Scope: `graduate_to_alpha_fix`
   Why: the old app history points to a stronger operator workflow than the current minimal export path.
   Add: presets, export naming controls, and explicit straight-alpha/premultiply handling notes.

## Later

1. Recover historical workflow features from screenshots and notes.
2. Rebuild batch comparison harness inside this repo instead of leaving it only in history.
3. Add clip-level benchmark reports under `test_runs`.
