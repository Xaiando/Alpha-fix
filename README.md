# Alpha Fix

Alpha Fix now has two parallel desktop apps inside this folder:

- `alpha_fix`: stable operator-facing branch.
- `alpha_fix_2`: sandbox branch for aggressive experimentation and debug-heavy previews.

Both apps are Python/OpenCV desktop tools for extracting OBS-ready overlays from stills or video.

## Current status (2026-07)

> The stable/sandbox roles below are **reversed** from current practice:
>
> - **`alpha_fix_2`** is the best-performing / main operator application.
> - **`alpha_fix`** is now the **research sandbox** — it hosts the newer overlay methods
>   `constellation` (Constellation Seeding + graded geodesic flood) and `bounded_geodesic`
>   (Bounded Geodesic Restoration: operator jurisdiction + Mahalanobis + geodesic + keep-walls).
>
> Full write-up of that work and the sweep-2 research boundary:
> [`documents/CONSTELLATION_AND_SWEEP2.md`](documents/CONSTELLATION_AND_SWEEP2.md).

## Branch Roles

`alpha_fix` keeps the conservative live workflow:

- `subject` mode uses a border-palette anchor matte plus EMA and LIPC.
- `overlay` mode uses the existing CHHC / auto-hole path.
- guided samples can now be drawn on the first frame and saved as JSON presets.
- exports PNG sequences plus optional media artifacts: `prores_4444`, `webm_alpha`, `chroma_mp4`

`alpha_fix_2` is the experimental branch:

- keeps the same subject baseline
- adds sandbox-only overlay method switching
- includes an `auto_hole` overlay experiment with hole-discovery debug views

## Run

```powershell
uv sync
uv run alpha-fix --gui
uv run alpha-fix-2 --gui
```

## Open Like An App

After `uv sync`, you can launch either app by double-clicking:

- `Alpha Fix.vbs` or `Alpha Fix.lnk`
- `Alpha Fix Sandbox.vbs` or `Alpha Fix Sandbox.lnk`

If the `.lnk` shortcuts are missing, run:

```powershell
powershell -ExecutionPolicy Bypass -File ".\Install Shortcuts.ps1"
```

CLI export examples:

```powershell
uv run alpha-fix --input "input.mp4" --output ".\\exports" --mode subject
uv run alpha-fix --input "input.png" --output ".\\exports" --mode overlay --sample-preset ".\\samples.json"
uv run alpha-fix --input "input.mp4" --output ".\\exports" --mode overlay --export-format prores_4444
uv run alpha-fix-2 --input "input.mp4" --output ".\\sandbox_exports" --mode overlay --overlay-method auto_hole
```

## Notes

- This is still a reconstructed codebase built from the research and history files, not the original recovered repo.
- Production and sandbox are intentionally split so experiments can move fast without destabilizing the operator path.
- `prores_4444` and `webm_alpha` carry real alpha and can look dark in normal players because they are previewed over black.
