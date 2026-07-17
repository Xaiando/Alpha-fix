# Sweep-2 Research Findings — Same-Colour Background Separation

Author: Claude · Date: 2026-07-17 · Status: **NEGATIVE RESULT (successful falsification)**

## Scope of the claim

> **Sweep-2 *global automation* is falsified under the current assumptions — the
> *concept* is not disproven.** This record exists so we do not re-run the same
> dead ends. Alternative signals remain open (see "Candidate directions").

Sweep 1 (chroma/green removal via the constellation method) is solved and shipped
(`alpha_fix/constellation.py`, `tests/test_constellation.py`). Sweep 2 is the hard
remainder: remove the **same-colour background** — corner fog and the mist *between
the pillars* (with distant spire silhouettes) — while keeping the **same-colour
decorative frame** and the character (Teledra). Reference asset:
`Hailuo_Image_Expand this image to 16_9 ...png` (5504×3072).

## Hypotheses tested and falsified

| # | Signal | Result | Evidence |
| - | ------ | ------ | -------- |
| H1 | Colour / diagonal Mahalanobis | **Falsified.** Mist and frame are the same dark blue; sampling the mist as background pulls the frame into the family and dissolves it. | Run-A/B `colour_rel`: mist ≈ frame once the family broadens. |
| H2 | Structure / entropy **threshold** | **Falsified.** No global cut separates them: mist + distant spires score ~0.35, *higher* than a flat pillar face (0.24) and equal to ornate carving (0.36). Two failure modes cancel: spires are textured (background with structure), frame faces are smooth (foreground without). | `scratchpad/structure_probe.py`, `sweep2_structure.png`. |
| H3 | Sharpness-barrier **geodesic flood** | **Falsified.** All smooth regions are globally connected, so a single mist seed drains the whole overlay (frame pillar leaked to α=0.24, the green flooded too). Barrier only holds at the crispest ornaments. | `scratchpad/sweep2_flood.py`, `sweep2_flood.png`. |

## What held (reusable truths)

- **Keep walls are absolute.** Teledra stayed α=1.000 through every experiment — the
  semantic-ownership problem is solvable by *marking* protected regions, not by any
  low-level signal (a smooth mask face and smooth background are indistinguishable to
  colour/structure alone; this is the "entropy cannot own semantics" caveat, confirmed).
- The mist and even soft spires **do** flood correctly *locally*; the failure is
  *unbounded spread*, not wrong local behaviour.

## Root cause

Mist-vs-frame is a **semantic** distinction ("distant scenery" vs "foreground
ornament"). No single low-level channel (colour, structure, focus-as-gradient) makes
it, and every smooth region is one connected basin, so any unbounded flood escapes.

## Dead ends — do NOT revisit

1. Sampling the mist as a colour background prototype (dissolves the frame).
2. A global structure/entropy threshold to classify mist vs frame.
3. An unbounded, single-seed sharpness/structure flood over the whole frame.

## Candidate directions (untested — for the swarm)

- **True focus/defocus estimation** (blur-scale / frequency falloff), not raw gradient —
  atmospheric haze genuinely softens the background; a proper defocus map may separate
  crisp frame edges from soft spire edges better than a Scholl/Scharr peak.
- **Monocular depth** (small depth model): background is *far*; depth is orthogonal to
  colour and structure.
- **Topology / enclosure**: the openings are holes enclosed by the *connected* frame,
  which is attached to the image border. Flood the **frame** from the border as a
  connected solid; background = "not reachable as frame."
- **Bounded operators**: operator roughly marks each opening; a *spatially bounded*
  edge-snap flood refines the boundary locally (no global leak). Highest-confidence
  tractable path; fits the fixed-geometry overlay use case.
- **Multi-signal fusion inside bounded regions** (colour + defocus + depth + enclosure).
- **Temporal (video)**: parallax and recurrence separate far background from near frame.

## Reusable assets

`alpha_fix/constellation.py` (`_geodesic_distance`, keep-wall handling); the probe
scripts under `scratchpad/`; this document.
