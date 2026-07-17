# Project Audit — 2026-06-11

**Auditor:** Claude
**Claim:** `verified` (every finding below was confirmed against code or a live run, not inferred)

## Verification snapshot

- `pytest tests` → **13/13 pass** (Linux sandbox, numpy 2.2.6, opencv 4.13)
- `python -m compileall alpha_fix alpha_fix_2` → clean
- `alpha-fix --help` / `alpha-fix-2 --help` → both OK
- ffmpeg exporters present in both apps

The codebase is healthy at the "does it run" level. The findings below are ordered by severity.

---

## P0 — Bugs and structural risk

### 1. Export-failure handler crashes with NameError (both apps)

`alpha_fix/gui.py:444-445` and `alpha_fix_2/gui.py:695-696`:

```python
except Exception as exc:
    self.after(0, lambda: messagebox.showerror("Export failed", str(exc)))
    self.after(0, lambda: self.status_var.set(f"Export failed: {exc}"))
```

Python unbinds `exc` when the `except` block exits. `self.after` runs the lambdas later on the Tk mainloop, after unbinding → `NameError: cannot access free variable 'exc'`. **This already fired in production**: `alpha_fix_sandbox_startup.log` (2026-05-18) shows exactly this crash at the then-line-456. The file grew since; the pattern survived at new line numbers in *both* GUIs. Net effect: when an export fails, the operator sees a NameError instead of the real error.

Fix (2 lines per file): capture before deferring —

```python
except Exception as exc:
    msg = str(exc)
    self.after(0, lambda: messagebox.showerror("Export failed", msg))
    self.after(0, lambda: self.status_var.set(f"Export failed: {msg}"))
```

### 2. No version control

There is no `.git` in the workspace. Three agents edit this tree concurrently with no diffs, no rollback, no blame, and no way to verify "promoted X to production" claims. This is the single highest-leverage process fix available: `git init` + initial commit + commit-per-ticket. The `.sync` protocol gives you messages; git gives you evidence.

---

## P1 — Divergence between production and sandbox

### 3. Promoted `auto_hole` is not the sandbox `auto_hole`

Codex's 2026-05-13 22:58 message promoted `auto_hole` to production claiming "production and sandbox now produce the same overlay result on the test still asset." That was true for that asset, but the code paths differ:

- **Flood barrier:** production `_grow_holes` receives `frame_fill` as the barrier (`pipeline.py:409` → flood can grow anywhere inside the frame within `hole_flood_tol=18` gray levels). Sandbox passes `void_mask` (`alpha_fix_2/pipeline.py:473` → growth restricted to dark/flat pixels). The sandbox version is the one hardened against the "frame_fill expands to nearly the full frame" blocker on the status board; production still has the looser behavior.
- **Border cleanup:** sandbox forces the outer 8 px transparent in overlay mode (`alpha_fix_2/pipeline.py:140-145`); production does not.

Recommendation: decide which barrier semantics is correct, port it, and add a parity test that runs both processors on the same synthetic overlay and asserts matching hole masks.

### 4. ffmpeg encode logic duplicated and already drifting

`alpha_fix/exporters.py` and `alpha_fix_2/service.py:284-310` each hand-roll the same three codec command sets (chroma_mp4 / prores_4444 / webm_alpha) with different output naming and structure. Next codec-flag fix will land in one and not the other. Extract one shared encoder module.

### 5. Export format is config-driven in prod, arg-driven in sandbox

`AlphaFixConfig.export_format` exists; `AlphaFix2Config` has no such field (format flows through CLI/GUI args). Harmless today, but presets/configs saved in one app are not expressible in the other.

---

## P2 — Hygiene

6. **Dead code:** `init_radiation_state`, `update_radiation_state`, and `_rad_state` are imported/declared in `alpha_fix_2/pipeline.py` but never used — the temporal radfield update was never wired; frame-1 fields plus change-mask gating do the work instead. Also a stray debug `print()` in the checkerboard path (`alpha_fix_2/pipeline.py:871`).
7. **Clutter:** `scratch/` holds ~40 ad-hoc test scripts plus output PNGs; `test_hevc.mp4` is 0 bytes; root has loose `compare_subject.py`, `extract_overlays.py`, `test_rad.py`. Fine as a lab bench, but worth a sweep once git exists so deletions are recoverable.
8. **`error_report.py` is Windows-only** (`ctypes.windll`). Correct for the target platform; just don't call it from cross-platform test code.

---

## Coordination findings

9. **Status board is a month stale.** `STATUS_BOARD.md` and `DECISIONS.md` say 2026-05-13, but checkerboard keyer, chroma key, despill, OSA-v2, anchor_blend, batch export, and the install/ launchers all landed May 14–23. The D-005 claim-label discipline stopped being applied right after it was written.
10. **Ticket drift:** `.sync/active_codex/04_ffmpeg_exporters.md` is still "active" though exporters shipped and are covered by `test_service_invokes_media_exporter_for_non_png_format`. Move to `/done/`.
11. **Backlog 05 (metrics/ablation discipline) is the most expensive open item.** Four new keyer methods (checkerboard, chroma, OSA-v2, SDR-Pow) landed with zero metric tables — exactly the failure mode that ticket was written to prevent. No new method should be promoted until the comparison harness exists.
12. **Channel state:** `Antigravity.md` was emptied (May 18), `codex.md` is gone, `.sync/messages/` is the live channel. My check-in #2/#3 questions in `claude.md` are stale — consider them withdrawn; the WHITE_BG_PRESET proposal from check-in #3 was never implemented and remains available if white-on-white subjects return as a priority.

## Test-coverage gaps (would have caught the above)

- No test exercises the GUI export-failure path (finding 1).
- No prod-vs-sandbox `auto_hole` parity test (finding 3).
- No white-on-white subject regression asset.

## Recommended order of work

1. Fix the `exc` NameError in both GUIs (4 lines total).
2. `git init`, commit everything, commit per ticket from now on.
3. Reconcile `auto_hole` barrier semantics + parity test.
4. Refresh STATUS_BOARD; move ticket 04 to done.
5. Build the metrics harness (backlog 05) before the next method lands.

— Claude
