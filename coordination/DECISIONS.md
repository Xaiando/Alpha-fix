# Decisions

Last updated: 2026-05-13 15:45:00 +02:00

## D-001

Decision:
- Keep two packages in the rebuilt workspace: `alpha_fix` and `alpha_fix_2`.

Reason:
- Production and sandbox need different risk tolerances.

## D-002

Decision:
- Treat subject extraction and overlay extraction as separate topologies.

Reason:
- Historical notes and real tests both show island and donut cases need different logic.

## D-003

Decision:
- Experimental math and overlay topology changes stay sandbox-first until verified.

Reason:
- The current repo is reconstructed and needs discipline around promotion.

## D-004

Decision:
- Shared truth lives in `coordination/*.md`; personal logs are secondary.

Reason:
- Free-form journals are too easy to let drift from the actual code state.

## D-005

Decision:
- Claims must be labeled `proposal`, `implemented`, `verified`, or `blocked`.

Reason:
- This keeps speculation, landed work, and test evidence from being mixed together.

## D-006  (Claude, 2026-07-17)

Decision:
- Reverse the historical roles: `alpha_fix_2` is the operator's known-good app; use
  `alpha_fix` (v1) as the sandbox for the new "Constellation Seeding + geodesic flood"
  overlay method. `alpha_fix_2` stays frozen during this work.

Reason:
- Owner directive. v2 currently works well and should not be destabilized. Note this
  contradicts the README's stable/sandbox labels, which are stale.

## D-007  (Claude, 2026-07-17)  — status: verified (synthetic)

Decision:
- Land MVP-1 of the constellation overlay method in `alpha_fix/constellation.py`, behind
  `--overlay-method constellation`. Colour (diagonal Mahalanobis vs the sampled background
  family) acts as a *gate* (off-family = wall), never as a per-step travel cost; the flood
  is an exact multi-source geodesic Dijkstra whose only travel cost is an edge barrier;
  a global scout teleports one seed dot per disconnected on-family basin.

Reason:
- Colour-as-travel-cost and any nonzero flat-region cost accumulate over distance and
  strand large basins (found and fixed during bring-up). Thresholds are calibrated
  relative to the sampled family's own spread so they transfer across images.
- Verified on the synthetic two-window scene (`tests/test_constellation.py`): operator
  window and the *uncircled* window both flood transparent, the dark wall and off-family
  lamp stay opaque, and disabling the scout leaves the uncircled window opaque.

Deferred (not yet built): entropy veto, superpixels, multi-prototype clean->fog family,
temporal/video evidence, conservative model self-training. Pure-Python Dijkstra runs at a
downscaled `const_work_res`; scikit-image `MCP_Geometric` is the production upgrade.

## D-008  (Claude, 2026-07-17)  — status: verified (synthetic)

Decision:
- Colour cost is a *transition* cost, not a per-step terrain toll. Three zones by
  `colour_rel` (Mahalanobis sigma / sampled-family spread): trusted (< trust) free;
  uncertain (trust..gate) crossed by paying a bounded cost at the family *boundary*
  (gradient of colour_rel), so a large uniform fog basin is charged once at its edge
  and its interior is free; rejected (>= gate) is a hard wall. Sol's per-step "swamp"
  toll is kept as `const_uncertainty_weight` but defaults to 0.

Reason:
- A bounded *per-step* toll still accumulates with depth, so large fog (the real
  asset's actual problem, not a thin transition) would exceed tau. Charging at
  transitions delivers "count boundaries crossed, not pixels travelled."
- `tests/test_constellation.py` now proves all 7 co-design cases, including #6 (deep,
  unsampled fog crossed via one bounded transition) and #7 (distant clean green not
  killed by distance). Full suite 17/17.

Known gap (for the entropy pass): a *gradual continuous* colour drift toward a
foreground of similar colour can leak until it crosses the absolute gate; entropy /
structure resistance is the intended second backstop.

## D-010  (Claude, 2026-07-17)  — status: shipped (sweep-2 deliverable)

Decision:
- Ship **Bounded Geodesic Restoration** as `overlay_method="bounded_geodesic"`. New
  `basin` sample kind = operator JURISDICTION: the flood only acts inside it and never
  touches the rest of the frame, whatever its colour. Inside jurisdiction it is the full
  constellation stack — Mahalanobis family (learned from a confirmed sample) + scout +
  graded geodesic flood + full-res colour snap — with keep-marks as absolute walls and
  large-scale entropy as a WEAK confidence modifier (never a judge).

Principle: the operator supplies semantic jurisdiction; the mathematics supplies precision.

Reason:
- Sweep-2 same-colour separation is unsolvable by any single low-level signal (D-009).
  Jurisdiction sidesteps the global-leak failure: it needs one bit of human meaning
  ("removable background lives here") and then the maths is precise. Validated on the
  real frame: mist removed inside the box, lantern kept (keep-mark), pillar/green/
  character outside the box untouched. `tests/test_bounded_geodesic.py` (suite 19/19).
- NN monocular depth stays PARKED (D-009): a research adviser, not a dependency to add now.

Automation roadmap (learn locally under supervision, then propose globally):
  Stage 1 detect only inside the box (shipped) → Stage 2 scout proposes matching
  constellations elsewhere but does NOT remove → Stage 3 operator approves each new
  colony → Stage 4 auto-accept only very-high-confidence matches → Stage 5 full-image
  automation with uncertainty returned for review. Only operator-approved pixels ever
  become new background signature, so a lantern that resembles fog cannot silently
  broaden the family (no model poisoning).

## D-009  (Claude, 2026-07-17)  — status: falsified (negative result recorded)

Decision:
- Record sweep-2 (same-colour background: corner fog + between-pillar mist) global
  automation as **falsified under current assumptions** — NOT the concept itself.
  Full record: `coordination/SWEEP2_FINDINGS.md`.

Reason:
- Three independent falsifications on the real asset: colour (mist == frame colour),
  structure threshold (mist+spires score >= frame), and unbounded sharpness flood
  (drains the whole overlay through connected smooth regions). Keep walls held
  throughout (Teledra α=1.000). Verified by `scratchpad/structure_probe.py` and
  `scratchpad/sweep2_flood.py`.
- Do NOT revisit the three dead ends. Open directions (defocus, monocular depth,
  frame-topology/enclosure, bounded operators, temporal) are logged for the swarm to
  investigate independently. This is a knowledge-base entry to prevent re-running the
  same experiments.
