# Constellation Overlay & Bounded Geodesic Restoration — Research & Deliverable

*Canonical documentation for the overlay-matting work in `alpha_fix/` (v1 research
sandbox). Written 2026-07-17. Companion detail lives in `coordination/`: the decision
log (`DECISIONS.md`), the sweep-2 findings and swarm report, the MISTLE arc, and the
narrative commentary. Reproducible experiments are in `scratch/*.py`.*

---

## Project state (2026-07)

- **`alpha_fix_2`** is the best-performing / main operator application.
- **`alpha_fix`** is now the **research sandbox** (this work lives here). *This reverses
  the older README stable/sandbox labels — see `coordination/DECISIONS.md` D-006.*
- **Bounded Geodesic Restoration** is the practical **sweep-2 deliverable**.
- **MISTLE** is a **validated structural adviser**, not an autonomous final judge.
- **Same-material mist/frame separation** requires **operator meaning**, a reusable
  authored matte, or a future semantic/depth model — it is not recoverable from the
  low-level pixel signals we tested.

---

## The problem

Extract OBS-ready alpha mattes from AI-generated overlay frames, where the generator
smears, mixes, and gradients the background so a plain chroma key fails. Two sweeps:

- **Sweep 1 — chroma/fog removal:** remove the green screen *and* its fogged/gradient
  variants *and* disconnected green panels, while keeping the ornate frame, hanging
  lamps, and the character. **Solved.**
- **Sweep 2 — same-colour background:** remove the misty background in the corners and
  *between the pillars* (with distant spire silhouettes) that is the **same dark colour
  as the frame you keep**. **Not solvable by low-level automation** (see the boundary
  below); shipped as an operator-guided tool.

---

## What shipped (two overlay methods in `alpha_fix`)

Both are selected via `--overlay-method` (CLI) or the config, and both are seeded from
operator sample regions (`background`, `keep`, and — new — `basin`).

### 1. `constellation` — Constellation Seeding + graded geodesic flood (sweep 1)

> *"The scout may teleport; the colonies must walk."*

- **Scout** teleports a background seed dot into every disconnected on-family basin
  (solves the "more than two green regions" problem — the disconnected panel is found
  without an operator circle there).
- **Colonies walk** an exact multi-source geodesic Dijkstra flood.
- **Colour is a graded gate, charged at *transitions*, not per pixel:** trusted family
  travels free; crossing into fog costs a bounded amount **once at the boundary** (so a
  large uniform fog basin is crossed at its edge and its interior is free); clearly
  foreign colour is an outright wall. *(This fixed the original per-pixel-cost bug the
  synthetic test caught — travelling through good background must never accumulate cost.)*
- **Full-resolution colour snap** re-sharpens edges and re-protects thin off-family
  structures (icicle tips, chains, droplets) that the downscaled flood eroded.
- Validated on the real gothic frame: removes green + fog + the disconnected panel,
  keeps frame/lamps/character. Tests: `tests/test_constellation.py`.

### 2. `bounded_geodesic` — Bounded Geodesic Restoration (sweep 2)

> *"The operator supplies semantic jurisdiction; the mathematics supplies precision."*

- A new **`basin`** sample kind grants the algorithm **jurisdiction**: it only removes
  material inside the operator's rough box and **never touches the rest of the frame**,
  whatever its colour.
- Inside jurisdiction it is the full constellation stack (Mahalanobis family + scout +
  graded geodesic + full-res snap), with **keep-marks as absolute walls** and
  **large-scale entropy as a weak confidence modifier** (an adviser, never a judge).
- Validated on the real frame: far-left mist removed inside the box, lantern kept via a
  keep-mark, and pillar / green / character *outside* the box untouched. Tests:
  `tests/test_bounded_geodesic.py`.
- **Acceptance note:** residual specks left un-removed inside the jurisdiction are
  intended scene **particles** (droplets/sparkles) — preserving them is correct; do not
  tune them away (`DECISIONS.md` D-010).

**Usage sketch** (operator marks regions, saved as a sample preset JSON):

```powershell
uv run alpha-fix --input frame.png --output .\exports --mode overlay `
  --overlay-method bounded_geodesic --sample-preset samples.json
```

`samples.json` carries `background` (a confirmed sample), `basin` (the rough opening),
and `keep` (props/character) regions. The frame's geometry is fixed, so a preset is
authored once and reused across frames and video.

---

## The division of labour (the architecture the research produced)

1. **The operator supplies the semantic bit** — *keep this pillar; removable background
   lives in this box.* The smallest amount of human meaning.
2. **The bounded solver** makes the thousands of precise pixel decisions inside that
   jurisdiction.
3. **MISTLE** identifies where the solver should **distrust itself** (structurally
   fragile background claims) — an adviser for the automation roadmap.
4. **Pinball** may later improve **coverage** around already-known obstacles.

This is not settling for manual removal; it is finding the *minimum* human meaning
needed to unlock reliable automation everywhere else.

---

## The research boundary (sweep-2 automation)

We attacked "same-colour mist vs same-colour frame" from every angle and mapped exactly
where it stops. Falsified, with measured evidence (`SWEEP2_FINDINGS.md`,
`SWEEP2_SWARM_REPORT.md`): **colour/Mahalanobis, structure/entropy threshold, unbounded
sharpness flood, atmospheric haze, focus/defocus, classical depth-proxy, and
topology/enclosure.** Two things held: **keep-walls are absolute**, and **bounding stops
the global leak**.

### MISTLE — the one genuine algorithmic win (as an adviser)

MISTLE (*Multiworld Image Segmentation Through Link Erosion*) asks a **structural**
question instead of an appearance one: not "can the flood reach this pixel once?" but
"can it *still* reach it after we repeatedly sabotage the uncertain passages?" True
background survives (redundant routes); a leak through one weak gap collapses.

- **Synthetic: clean win.** On fog + a same-colour pillar behind a dark border with a
  4px gap, the flood leaks the pillar and even ordinary voting is fooled (Q_ord 0.95),
  but bridge-sabotage collapses it (Q_sab 0) → ΔQ 0.95 vs true fog 0.00.
- **Real frame: a validated adviser, not a solo solver.** Per-neck graded sabotage fixes
  over-flagging but is too gentle to catch the fog-coloured pillar gap; route-diversity
  flags the pillar but *distal legitimate mist is one-route too*; and **enclosure** has
  no frame material to build a shell from, because the same-coloured frame is classified
  as background family. The mist and the pillar are the **same material**; the
  distinction is **semantic**.

**Verdict:** MISTLE correctly *exposed where the decision becomes semantic rather than
recoverable from the tested pixel signals.* That boundary is itself a valuable result.
It remains a validated pre-filter/adviser for later automation stages, where a *proposed
new* background actually differs from the frame.

### Pinball — not falsified

**Geodesic Pinball** (wall-crawler seeds that creep behind props through narrow passages,
with continuous valid ancestry back to the seed) was never a mist-vs-pillar *classifier*
and is **not** falsified here. It solves *coverage* around known props — clearing
legitimate background behind a lantern once the keep geometry is known — and stays viable
as a bounded coverage specialist for a future thread.

### Parked frontier

**NN monocular depth** (background far vs frame near) is the one untested orthogonal
signal with a physical reason to work; it needs a model dependency (torch + weights) the
current stack deliberately avoids. Parked as optional research (`DECISIONS.md` D-009).

---

## Reproducing the research

All probes are dependency-free (numpy + opencv) and deterministic under a fixed RNG seed:

- `scratch/mistle_probe.py` — MISTLE synthetic validation (ΔQ 0.95).
- `scratch/real_mistle.py` — real-frame audit (binary sabotage over-flags).
- `scratch/graded_mistle.py` — graded per-neck sabotage + route diversity.
- `scratch/enclosure_probe.py`, `scratch/enclosure_viz.py` — persistent shell adjudication.

Test suite: `uv run python -m unittest discover -s tests` (constellation + bounded
geodesic guards among the suite).

---

## Index of detail

| Document | Contents |
| -------- | -------- |
| `coordination/DECISIONS.md` | D-006…D-011: role reversal, constellation, edge-fidelity, sweep-2 falsification, bounded geodesic, particle acceptance, MISTLE. |
| `coordination/SWEEP2_FINDINGS.md` | The eight falsified approaches with evidence; dead-ends; candidate directions. |
| `coordination/SWEEP2_SWARM_REPORT.md` | Ranked signal investigation (haze/focus/depth/topology/entropy/bounded-operator). |
| `coordination/MISTLE_FINDINGS.md` | The full MISTLE arc: synthetic win → real-frame limits → enclosure → boundary. |
| `coordination/SWEEP2_COMMENTARY.md` | The narrative "we tried, and here's what it did." |
