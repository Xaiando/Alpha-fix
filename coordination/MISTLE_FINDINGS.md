# MISTLE — Multiworld Image Segmentation Through Link Erosion

Author: Claude (idea: operator) · Date: 2026-07-17 · Status: **VALIDATED (positive result)** on the decisive synthetic.

The first sweep-2 direction to pass. Where every appearance signal failed (colour,
structure, focus, haze, depth-proxy, topology — see `SWEEP2_FINDINGS.md`), MISTLE
succeeds by asking a *structural* question instead of an appearance one.

## The principle

Do not ask whether the background flood can reach a pixel **once**. Ask whether it can
**still** reach it after we repeatedly sabotage the questionable passages.

- A broad fog field has many alternative routes → **survives sabotage**.
- A false leak into a pillar/lantern usually depends on one fragile passage → **collapses**.

This is NOT ensemble voting ("how many segmenters say background?"). It is an
**adversarial connectivity audit**: how structurally dependent is the background claim
on particular passages. Two pixels can both poll 90% background; MISTLE attacks the
bridge and finds one has twenty redundant routes and the other has one weak door.

## Decisive test (passed)

Synthetic (`scratch/mistle_probe.py`, deterministic under a fixed RNG seed): a broad
fog basin + a smooth **same-colour** pillar enclosed by a dark border with **one 4px
weak gap** + thin props + fog seeds. Classes from Mahalanobis + distance-to-wall:
trusted interior (always open), uncertain near-wall band incl. the gap (perturbed),
walls (never open). 64 worlds open uncertain passages with p=0.85; the sabotage batch
closes them all. `Q = fraction of worlds reachable`, `ΔQ = Q_ordinary − Q_sabotaged`.

| region | deterministic baseline | Q_ord | Q_sab | ΔQ |
| ------ | ---------------------- | ----- | ----- | -- |
| fog (should remove) | removed ✓ | 1.00 | 1.00 | **+0.00** |
| pillar (leak; should keep) | **removed ✗ (leak)** | **0.95** | 0.00 | **+0.95** |

The baseline leaks the pillar; ordinary voting is *also* fooled (Q_ord 0.95); MISTLE's
sabotage collapses it to 0, so ΔQ=0.95 flags the leak while true fog sits at ΔQ=0.00.
The MISTLE alpha keeps the pillar and removes the fog. Hypothesis confirmed:
**ΔQ small for true background, large for a leak through a weak passage.**

## Why it is (probably) novel

Seeded random-walker and probabilistic watershed already put probabilities on weighted
graphs, but their probability comes from diffusion / hitting times / distributions over
spanning forests. MISTLE's signal is **connectivity survival under controlled stochastic
destruction of uncertain links**, plus explicit **bridge fragility (ΔQ)** and seed
dropout. That specific adversarial-connectivity framing is the part not found in a
targeted search of primary research (internals of proprietary products are undisclosed).

## What it cannot do (honest bound)

If a smooth foreground region has the same statistics as the background, no enclosing
boundary, broad redundant connectivity to the sample, and no keep-mark, MISTLE has no
hidden information to recover and may still remove it. It attacks the *narrow, real*
failure: **false removal caused by one or a few weak passages through a meaningful
border** — exactly what the bounded operator currently struggles with.

## Proposed role: a reliability tribunal (after the bounded flood)

1. Bounded Geodesic Restoration / GrabCut proposes the removable region.
2. MISTLE builds alternate worlds around that proposal.
3. Structurally-stable background is accepted; fragile leaks rolled back.
4. Volatile boundaries become soft-alpha bands (boundary volatility across worlds).
5. Approved pixels train future constellation scouting (no poisoning — approved only).

GrabCut asks "what is the best partition?"; MISTLE asks "would that partition survive if
several assumptions were slightly wrong?" — an algorithm that can **doubt its own matte**.

## Real-frame audit (2026-07-17) — partial pass; do NOT integrate yet

Isolated audit on the gothic frame (`scratch/real_mistle.py`), same jurisdiction/sample
as the bounded-operator leak. Passage/wall = off-family colour OR crisp L-edge, so the
same-colour pillar is enclosed by its own silhouette. Baseline bounded flood leaks the
pillar (0.75 removed). Then Q_ord, Q_sab, ΔQ over 5 regions × 3 seeds × 5 parameter sets
(work-res 480/640/800, edge threshold, band D, sabotage p, seed dropout).

- **PASS (leak detection):** the leaked pillar is robustly fragile — ΔQ 0.59–0.69,
  Q_sab→0, essentially identical across every seed and perturbation. The pillar-leak IS
  structurally brittle and MISTLE catches it. Lantern/chain also high-ΔQ (contested —
  correct for route-dependent props). Nothing outside the jurisdiction touched.
- **NOT PASS (fog resilience):** full-strength sabotage (close ALL uncertain passages)
  **over-flags legitimate narrow mist**. The real mist strip is thin and criss-crossed by
  ornament edges, so "trusted" (far-from-edge) pixels are sparse and trusted-only
  connectivity reaches the mist only near the seed. Q_sab is high only near the seed; most
  genuine mist collapses → a large "contested" zone, not a clean remove/keep split. The
  table's "true_mist ΔQ 0.11–0.26" was a near-seed box; broader mist reads contested.

Verdict: MISTLE's fragility detection is real and generalizes for the LEAK, but the
current construction fails the operator's integration gate (pillar fragile AND fog
resilient) because it also flags legitimate narrow corridors. Confirms the operator's
own caution. The 3-state OUTPUT (robust-bg / robust-non-bg / contested → adjudicate) is
validated as necessary; on the real frame the contested zone is large, so adjudication
specialists are essential, not optional.

Indicated refinement (before any integration): **graded sabotage** — close only the
*narrowest / lowest-confidence* bottlenecks (e.g. distance-to-wall ≤ 1–2, or a passage
confidence below a cutoff), not every uncertain link, so wide-enough legitimate corridors
survive while the pillar's true bottleneck still closes. Re-test whether legit mist regains
resilience while the pillar stays fragile. Also consider per-pixel route-diversity /
seed-of-arrival tracking so wide mist scores redundant even when far from the seed.

## Next / related

- **Validate on the real gothic frame's actual pillar-leak** before integrating.
- **Geodesic Pinball** (operator idea): wall-crawler seeds that creep behind props
  through narrow passages with "receipts" (continuous valid ancestry path). Complementary
  coverage tool; deferred until MISTLE integration. Its dubious one-pixel routes are
  themselves exactly what MISTLE should audit.
