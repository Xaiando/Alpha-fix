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

## Next / related

- **Validate on the real gothic frame's actual pillar-leak** before integrating.
- **Geodesic Pinball** (operator idea): wall-crawler seeds that creep behind props
  through narrow passages with "receipts" (continuous valid ancestry path). Complementary
  coverage tool; deferred until MISTLE integration. Its dubious one-pixel routes are
  themselves exactly what MISTLE should audit.
