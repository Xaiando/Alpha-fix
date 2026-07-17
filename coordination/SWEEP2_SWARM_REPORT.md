# Sweep-2 Signal Investigation — Ranked Report

Run manually (swarm hit the session limit after 1 probe), same measured methodology.
Author: Claude · Date: 2026-07-17 · Companion to `SWEEP2_FINDINGS.md`.

**Question:** does any signal separate the misty same-colour background (corner fog +
between-pillar mist, incl. distant spires) from the decorative frame we keep, without
removing the character (Teledra)? Measured on the real 5504×3072 frame, signal means
in labelled mist / frame / character boxes; "separates" = a single threshold puts all
mist on one side, all frame on the other, character on the keep side.

## Results (ranked)

| Signal | Verdict | Key evidence |
| ------ | ------- | ------------ |
| **Bounded operator** (rough opening box + local edge-snap) | **PARTIAL — useful** | Containment works: nothing *outside* the box leaks (frame/green/character = 1.000), and crisp objects (lantern, chain) are preserved. But *inside* the box the smooth pillar face is still eaten (α 0.37) once the flood finds a soft spot. Safety mechanism, not full automation. |
| **Multiscale entropy** (k=21, 61) | **WEAK / fragile** | A *thin* positive gap: mist entropy 0.90–1.31 sits just below frame 1.04–1.92, character on keep side. But the margin is ~+0.03–0.04 (~3%) with hand-picked boxes; single-scale (k7) already fails (−0.007). Not reliable alone; possible soft tie-breaker only. |
| Focus / defocus (tenengrad, hf-ratio) | **FAIL** | Gaps −1.36 / −0.12. Ornate carving is sharp (keep) but flat pillar faces are as soft as mist, and soft spires read low too. Same flat-face/textured-spire cancellation as the structure threshold. |
| Depth proxy (classical: defocus/dark-channel) | **FAIL** | Gap −0.09; ≈ defocus inverted. A *real* NN depth model (background far vs frame near) is the one untested orthogonal signal — but needs torch + weights (Depth-Anything/MiDaS), not available offline. |
| Haze / atmospheric perspective | **FAIL** | (swarm) All four channels negative-margin; shadowed frame stone mimics haze; blue-shift & dark-channel run *opposite*; character in the remove cluster. See H4. |
| Topology / enclosure (frame = border-connected solid) | **FAIL** | Green window & panel come out as holes (already handled), but the mist *touches the image border* → not enclosed → uncaught (0.00–0.15), and the **character reads as an enclosed hole (0.76) → would be removed**. Disqualifying. |

## Conclusion

No single low-level signal separates mist from the same-colour frame — now confirmed
across **eight** approaches (colour, structure-threshold, unbounded sharpness flood,
haze, focus, classical-depth, topology, and multiscale-entropy-as-primary). The two
non-failures are about **containment and marking**, not detection:

- **Keep-walls are absolute** — the only thing that reliably protects Teledra is
  *marking* it. Every detector, including topology, otherwise eats part of the character.
- **Bounding stops the global leak** — the operator's jurisdiction box makes the
  sharpness flood *safe*, and it does preserve crisp isolated ornaments.

## Recommendation (for trimming)

- **Pursue — practical:** operator-guided sweep-2 for the *fixed* frame. Mark the
  openings + the frame keep-regions inside them **once** → reusable preset; the bounded
  sharpness flood adds crisp-edge refinement (great on lanterns/chains). Robust, ships.
- **Park — weak aux:** multiscale entropy (large scale) as a soft tie-breaker *inside*
  a bounded region only; never primary.
- **One real frontier:** NN **monocular depth** — the only orthogonal signal untested,
  and the only one with a physical reason to separate far background from near frame.
  Cost: a model dependency (torch + weights) the current stack deliberately avoids.
- **Dead — do not revisit:** colour, structure/entropy threshold, unbounded sharpness
  flood, haze/atmospheric perspective, focus/defocus, classical depth proxy, topology/
  enclosure.
