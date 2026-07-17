# Status Board

Last updated: 2026-07-17 (Claude)

> Role note (Claude, 2026-07-17): per owner directive, `alpha_fix_2` is the known-good app
> and `alpha_fix` (v1) is now the sandbox for the constellation overlay work. This reverses
> the README's stable/sandbox labels. See DECISIONS D-006.

## Active Lanes

| Lane | Scope | Owner | Status | Current Evidence | Next Action |
| --- | --- | --- | --- | --- | --- |
| Constellation overlay (v1 sandbox) | `alpha_fix` | Claude | implemented + validated on real frame | `--overlay-method constellation`; scout + geodesic flood + graded colour transition; removes green+fog+disconnected panel, keeps frame/character/lamps | sweep-1 edge-fidelity pass (full-res colour snap) |
| Sweep-2 same-colour bg (research) | `alpha_fix` | Claude | **falsified (negative result)** | global automation dead-ends recorded in `coordination/SWEEP2_FINDINGS.md` + `SWEEP2_SWARM_REPORT.md` (8 approaches); keep walls held | NN monocular depth parked as optional frontier |
| Bounded Geodesic Restoration (sweep-2 deliverable) | `alpha_fix` | Claude | shipped | `overlay_method=bounded_geodesic`; `basin` jurisdiction + Mahalanobis + geodesic + full-res snap + weak entropy; validated on real frame (mist removed in-box, props/outside kept); `tests/test_bounded_geodesic.py` (19/19) | automation roadmap Stage 2: scout proposes globally, operator approves |
| Production stability | `graduate_to_alpha_fix` | Codex | active | `alpha_fix` runs, tests pass, CHHC margin typing fixed | rebuild guided sampling workflow from historical UI |
| Sandbox overlay topology | `sandbox_only_alpha_fix_2` | Codex + Antigravity | active | `auto_hole` finds seeds, but still opens wrong regions on real overlay still | improve seed ranking and outer-frame model |
| Sandbox debug UX | `sandbox_only_alpha_fix_2` | Codex | implemented | seed map and frame mask are now visible in sandbox GUI | validate on real overlay clips |
| Transition-zone math | `sandbox_only_alpha_fix_2` | Antigravity | proposed | `SDR-Pow` exists, `OSA-v2` exists, neither has branch-level validation metrics yet | run explicit ablations before promotion |
| Coordination system | `coordination_only` | Codex | implemented | protocol, board, decision log, backlog, and handoff template created | use them consistently in future check-ins |

## Immediate Blockers

- Overlay real-asset failure is no longer "no seeds"; it is "wrong seeds".
- `frame_fill` in `auto_hole` still expands to nearly the full frame on the tested still asset.
- Historical guided sample workflow from the old GUI is not rebuilt yet in production.

## Verification Snapshot

- `uv run python -m unittest discover -s tests -v`
- `uv run alpha-fix --help`
- `uv run alpha-fix-2 --help`
- `uv run python -m compileall alpha_fix alpha_fix_2`
- real still-image smoke export passed for both apps

## Next Team Focus

1. Improve sandbox hole selection quality.
2. Add production-style guided sample workflow instead of border-only inference.
3. Expand metrics so experimental math is compared against actual evidence, not descriptions.
