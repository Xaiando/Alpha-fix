# Constellation & the Fog — a research commentary

*A narrative companion to `SWEEP2_FINDINGS.md`. The findings file is the clinical
record; this is the story of how we got there, left for whoever picks this up next.*

## The idea

We wanted alpha-matte extraction that survives AI-generated overlays, where the
generator smears, mixes, and gradients the background so a plain chroma key fails.
The design that emerged had a nice shape: **the scout may teleport, the colonies
must walk.** A global scout drops seed dots wherever the sampled background family
reappears (even in disconnected basins); each seed then floods outward along a
geodesic cost field and stops at structural walls. Colour tells us *what plausibly
belongs* to the background; geodesics decide *what is reachable without crossing a
boundary*.

## Sweep 1 — it worked, and the synthetic earned its keep

The first implementation made a subtle, seductive mistake: it charged the flood a
per-pixel colour cost. That means travelling through perfectly good background
accumulates cost with distance — the algorithm treated *"far from the sample"* as
*"probably not background."* A distant-but-clean green pixel died simply because it
was distant. The synthetic test caught it immediately, before it hardened into the
architecture. That single catch is the whole argument for building the synthetic
first: propose, falsify, understand *why*, reformulate.

The reformulation: colour **gates**, it does not toll. Trusted family travels free;
the cost of crossing into fog is paid **once at the boundary** (a transition cost,
not a depth cost), so a large uniform fog basin is crossed at its edge and its
interior is free; clearly-foreign colour is an outright wall. On the real gothic
frame this removed the green, the fog gradient, *and* a disconnected green panel the
operator never circled (the scout found it), while keeping the frame, the hanging
lamps, and the character. An edge-fidelity pass — snapping the low-res flood back to
the full-resolution colour boundary — then recovered the thin icicles and chains.
Sweep 1 is real.

## Sweep 2 — the wall we did not get past

Then the hard half: the fog in the corners and *between the pillars* — the misty
scenery with distant spires that you want gone so the arch openings become
see-through. Here the whole approach hit a genuine wall, and it is worth being
honest about why, because the wall is instructive.

The mist is **the same colour as the frame we are keeping.** So we tried, in order:

- **Colour.** Blind by construction — sample the mist and the frame dissolves with it.
- **Structure/entropy, as a threshold.** Failed for a beautiful reason: two errors
  cancelled. The distant spires are *textured* (background that has structure), and
  the frame's flat faces are *smooth* (foreground that lacks it). The histogram of
  "detail" put mist and frame on top of each other.
- **A sharpness-barrier flood.** Failed the most vividly. Seeded in one corner of
  mist, it drained the entire overlay — because every smooth region is one connected
  basin, so a single seed walks through all of them, held back only by the crispest
  ornaments.

What *did* survive every attempt: the character. Keep-walls are absolute. And that is
the real lesson — the one the operator (Teledra) spotted watching a smooth white mask
get chroma-keyed away: **no low-level signal can decide semantic ownership.** A smooth
mask face and a smooth patch of sky are identical to colour, to entropy, to focus.
The only thing that reliably protects the mask is *marking* it. "Distant scenery vs
foreground ornament" is a semantic judgement, and we were asking arithmetic to make it.

## What we believe now

Sweep-2 *global automation* is falsified **under these assumptions** — not the
concept. We did not prove it is impossible; we proved that colour, a structure
threshold, and an unbounded single-signal flood do not do it, and we mapped exactly
where each one breaks. The promising, unspent directions are orthogonal signals
(true defocus, monocular depth), the *topology* of the frame (it is one connected
solid attached to the border; the openings are holes), and **bounded operators** —
letting the operator rough-mark each fixed opening and only asking the algorithm to
snap the local boundary, which sidesteps the global-leak failure entirely and fits
the fact that an overlay frame is static geometry.

We tried. It did that. The map of the dead ends is now part of the repo so the next
attempt starts past them, not at them.

— Claude, 2026-07-17
