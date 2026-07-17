# Claude Handover — Constellation / Bounded Geodesic / Sweep-2 research

Date: 2026-07-17 · Author: Claude · Merge landed: `48f1352` on `main` · Tag:
`constellation-sweep2-research-v1`. This answers the reviewer's handover checklist and
confirms the P0 findings from the public-`main` scan.

---

## 0. Confirmed P0 / correctness findings (verified against source)

These are accurate; feed them straight into the Codex "blast walls" lane.

1. **Bounded jurisdiction "never outside the box" has three holes:**
   - `alpha_fix/pipeline.py` `process_frame` zeros the outer 8px for **all** overlay
     methods incl. `bounded_geodesic` (removes a border even when jurisdiction is far from it).
   - `alpha_fix/constellation.py`: the jurisdiction clamp (`membership_full *= jurisdiction_full`)
     is applied **before** the Gaussian feather, so the blur bleeds removal ~feather_px
     outside the basin.
   - `_apply_constellation` returns `self._apply_chhc(...)` (global) when there is no usable
     background model → `bounded_geodesic` silently falls back to a **global** operation.
   - Fixes: method-specific/configurable border cleanup; re-apply jurisdiction *after*
     feather; for `bounded_geodesic` require both a `basin` and a `background` sample else
     explicit error / opaque no-op; add tests for an object adjacent to the basin edge and
     decoration in the outer 8px.
2. **v2 basin schema hazard (real):** `alpha_fix_2/radfield.py:59-62` and `:176-179` treat
   any non-`"background"` region kind as keep radiation. A v1 preset containing a `basin`
   passed to v2 makes the basin **radiate opacity**. Fix: v2 explicitly ignores `basin`
   until supported; add a cross-package preset-compatibility test.
3. **v2 structurally inherits v1:** `AlphaFix2Processor(BaseProcessor=AlphaFixProcessor)`.
   Edits to v1 shared methods can silently change the known-good v2 app. Longer term:
   extract stable primitives into `alpha_core`; stop inheriting the research processor.
4. **Role reversal not on the product surface:** README opening bullets + "Branch Roles"
   still call v1 stable / v2 experimental; launchers/installer label v1 "Alpha Fix
   (Production)" and v2 "Alpha Fix Sandbox". A normal user launches the *experimental* app.
5. **Deliverable not usable from the GUI:** v1 GUI dropdown exposes only `auto_hole`/`chhc`;
   the sample editor offers only `background`/`keep`, not `basin`. The `ConstellationDebug`
   fields exist but `process_frame` requests only alpha and discards them.

I did **not** fix these — they belong to the Codex Lane A per the reviewer's plan. I can
take the two that are purely my code (bounded holes + v2 basin guard) if you want them done
now; say the word.

---

## 1. Real gothic-frame validation — commands & scripts

Run from repo root with `uv run python <script>`. **Committed to the repo** (`scratch/`):
`mistle_probe.py`, `real_mistle.py`, `graded_mistle.py`, `enclosure_probe.py`,
`enclosure_viz.py`.

**NOT on GitHub — local scratchpad only** (the ones that produced the shipped screenshots):
`run_real.py` (constellation real-frame + montage/heatmaps), `run_bounded.py`
(bounded_geodesic real-frame), `zoom_real.py` (full-res edge crops), `structure_probe.py`,
`sweep2_flood.py`, `inspect_sweep2.py`, `verify_constellation.py`, plus all PNG montages.
Path: `…\Temp\claude\…\scratchpad\`. I can commit parameterized copies of the two most
useful (`run_real.py`, `run_bounded.py`) if you want them reproducible on GitHub.

## 2. Private / uncommitted asset

- **`C:\Users\Kaged\Downloads\Hailuo_Image_Expand this image to 16_9 plea_486898290274779137.png`**
  (5504×3072). The real gothic frame. **Private, not committed** (correctly — user asset).
  Real-frame validations cannot be reproduced on GitHub without it. All coordinates below
  are **normalized [0..1]**, so they transfer to any similar overlay frame.

## 3. Sample presets / normalized coordinates used

- **Constellation** (`run_real.py`, "clean+fog"): bg ellipse `(0.28,0.52,0.36,0.60)` clean
  green; bg ellipse `(0.42,0.14,0.50,0.20)` top fog; keep ellipse `(0.82,0.62,0.95,0.95)`
  character.
- **Bounded geodesic** (`run_bounded.py`): basin rect `(0.0,0.05,0.105,0.86)`; bg ellipse
  `(0.015,0.44,0.055,0.58)` mist; keep ellipse `(0.055,0.30,0.105,0.47)` lantern; keep rect
  `(0.0,0.05,0.018,0.86)` frame column.
- **MISTLE / enclosure**: jurisdiction `(0.0,0.05,0.15,0.86)`, bg sample `(0.02,0.44,0.055,0.58)`.

## 4. Named ROIs (normalized [x0,y0,x1,y1])

mist: far_left `(0.02,0.45,0.09,0.70)`, tl_corner `(0.02,0.10,0.07,0.34)`, distant_spire
`(0.03,0.50,0.08,0.62)`, near `(0.02,0.55,0.05,0.70)`, middle `(0.02,0.28,0.05,0.42)`, far
`(0.015,0.09,0.045,0.20)`, behind_deco `(0.005,0.62,0.025,0.80)`. pillar `(0.115,0.42,0.14,0.68)`.
lantern `(0.07,0.34,0.10,0.44)`. chain `(0.086,0.16,0.099,0.30)`. character `(0.85,0.72,0.92,0.88)`.
green(out) `(0.30,0.55,0.45,0.68)`. **All hand-estimated by eye — approximate, not ground-truth.**

## 5. Parameters behind each result

- **Constellation defaults** (`alpha_fix/config.py`): work_res 640, edge_snap on, color_gate
  6.0, color_trust 1.5, color_weight 4.0, grad_weight 8.0, barrier_floor 0.5, tau_lo 2.0,
  tau_hi 30.0, feather 1.5, scout on, seed_color_tol 1.5, seed_grad_max 0.12,
  seed_min_area_frac 0.004.
- **Bounded geodesic** adds: basin_dilate 6, entropy_weight 0.25 (gated to this method),
  entropy_window 61.
- **MISTLE synthetic**: N=64 worlds, p_unc 0.85, trusted-band D 5px, 4px gap.
- **MISTLE real audit**: N 48–96, seeds {1,2,3}, swept work_res 480/640/800, edge_thresh,
  D, p_unc, seed dropout.
- **Graded MISTLE**: width bands (half-clearance@640 ≤1.25/2.25/3.5/5 → p 0.95/0.70/0.30/0.08/0),
  confidence modifier (c<0.35/0.55/0.75/0.90 → 1.0/0.75/0.40/0.15/0.05), p_close =
  p_width·(0.25+0.75·mod), per-**neck-component** closure, N=96, 3 seeds.
- **Enclosure**: closing radii 0/1/2/3/5 (viz also 6/12), edge_thresh 1.2/1.6.

## 6. Expected outputs / contact sheets

Montages produced (local scratchpad, sent to operator in chat, **not on GitHub**):
`constellation_proof.png`, `real_B_clean_plus_fog.png`, `real_B_zoom.png`, `run_bounded.png`,
`mistle_probe.png`, `real_mistle.png`, `sweep2_structure.png`, `sweep2_flood.png`,
`enclosure_viz.png`. Key numbers: bounded real-frame — mist α≈0.15, lantern 1.00, pillar/green/
character outside box 0.97–1.00. MISTLE synthetic — ΔQ pillar 0.95 vs fog 0.00.

## 7. Do-NOT-revisit (mapped dead ends)

Global colour/Mahalanobis; structure/entropy threshold; unbounded sharpness flood;
atmospheric haze (sat/contrast/blue-shift/dark-channel); focus/defocus; classical
depth-proxy; topology/enclosure as a global rule; naive "closed contour = keep"; more
entropy thresholds; auto-accepting global scout colonies without approval. **NN monocular
depth is parked** (optional future dependency). Full evidence: `SWEEP2_FINDINGS.md`,
`SWEEP2_SWARM_REPORT.md`, `MISTLE_FINDINGS.md`.

## 8. Performance timings (observed, Windows / RTX 5060 Ti box)

- Test suite: 19 tests ≈ 1.0s.
- Constellation on the 5504px frame at work_res 640 (pure-Python Dijkstra): ~a few seconds
  per flood; `run_real.py` (2 runs + heatmaps) well under a 200s cap.
- MISTLE worlds (connectedComponents, no Dijkstra): fast; 64–96 worlds ≈ seconds.
- Bounded geodesic real-frame: seconds.
- **Swarm hit the session usage limit** after 1 of 6 probes (~4 min, 356k subagent tokens);
  the remaining probes were completed manually in the main session.

## 9. Export failures observed in actual use

**None observed — I never exercised the export/FFmpeg path this session.** All work was
matte generation via `process_frame`/`constellation`. Gemini's export findings (#5 in its
scan: shared `rgba`/`alpha` dirs + unbounded `frame_%05d.png` → stale-frame contamination;
two drifting FFmpeg implementations) are **code-inspection inferences, not runtime-observed
by me** — flag them as "to be reproduced," not "confirmed in use."

## 10. Intended next experiment before the branch was closed

- **Stage 2 automation** — scout proposes matching colonies globally with shown reasons
  (Mahalanobis/entropy/area/route/MISTLE-fragility); operator approves; **proposals only, no
  auto-removal**; only approved pixels update the atlas.
- **Geodesic Pinball** — coverage behind known props via wall-crawlers with linked ancestry
  (viable, NOT falsified; not a mist-vs-pillar classifier).
- **GUI wiring** — expose constellation/bounded_geodesic + `basin` authoring + the
  `ConstellationDebug` panes (scout map, colour-rel, barrier, geodesic-D, membership).

## 11. Assumptions encoded only in conversation (not yet in docs)

- All ROI coords were **eyeballed** from the frame — approximate, not measured.
- The first real-frame MISTLE "true_mist ΔQ low" was a **near-seed** box; distal mist is
  worse (now caveated).
- The 19/19 tests use **synthetic geometry** (rects/circles/flat fields), guarding semantics
  (scout teleport, fog traversal, walls, keep, jurisdiction) — **not real-pixel quality**.
- Bounded-geodesic real-frame quality depends on **operator marking quality**; the shown
  result used the specific regions in §3.
- The pillar "leak" that motivated MISTLE was reproduced in a **standalone** sharpness-only,
  pillar-inside-box test; the shipped `bounded_geodesic` (keep-marks + colour family) behaves
  differently.
- Particle preservation is an **operator-confirmed acceptance criterion**, not a derived law.
- Repo shows LF↔CRLF warnings on Windows; committed blobs are LF.
