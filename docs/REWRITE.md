# Alpha Fix 3 rewrite

Date: 2026-09-11

The new project lives in `D:\Apps\Alpha fix`. It is self-contained after dependency installation. It does not import from or launch the old project at runtime.

## Preserved algorithms

The old project's controlling role decision identifies `alpha_fix_2` as the known-good operator app, despite its old sandbox labels. Its algorithm is now `engines/operator.py`. The original `alpha_fix` algorithms are now `engines/research.py`. Common numerical code was extracted into `engines/primitives.py`, so operator processing no longer inherits from a research processor.

Operator methods: subject extraction, automatic holes, CHHC, guided radiation, chroma key, and baked checkerboard removal. The existing halo suppression, temporal state, opacity adjustments and despill controls remain available in advanced settings.

Research methods: the original subject/automatic-hole/CHHC processing, constellation and bounded geodesic. The research selector makes these roles explicit. Basin regions can now be authored alongside background and keep regions. Bounded mode retains its opaque fallback when guidance is missing. Concurrent probe composition is retained as a tested engine utility, without a new research workflow being invented around it.

Source file SHA-256 hashes are recorded in `source-provenance.json`. The migration reused numerical methods; the user explicitly requested preserving them. GUI, project persistence, worker lifecycle, media I/O, CLI and exports are rewritten.

NumPy 2.4.4 and OpenCV 4.13.0.92 are pinned to the original project's lockfile and installed environment, so the rewrite also preserves the numerical library versions. The new desktop toolkit is PySide6, locked in `uv.lock`.

## New application structure

| Module | Responsibility |
| --- | --- |
| `project.py` | Versioned portable projects, per-file settings, configuration validation |
| `media.py` | Unicode-safe still-image reads/writes, sequential video decoding, discovery |
| `service.py` | Preview/export processing sessions, cancellation, encoding and isolated runs |
| `engines/` | Preserved processing algorithms and configuration defaults |
| `ui/` | PySide6 desktop workspace, drawing canvas, settings editor, background workers |
| `cli.py` | Headless export and GUI entry point |

The workspace includes drag-and-drop, a file queue, source/result wipe comparison, alpha and operator debug views, checkerboard/black/white/green compositing, zoom/pan, frame selection, rectangle/ellipse samples, preset import/export, individual and batch export, progress, cancellation, and editable projects.

Projects save per-file settings and samples using relative paths when practical. Old sample-only JSON presets still load; new presets include full processing settings. The app prompts to save unsaved project changes when closing or opening another project.

## Export behavior

Every export writes to an owned temporary folder under the selected destination, then renames that folder to a unique completed run. Existing outputs are preserved. Cancelling or failing removes only that invocation's staging folder. A completed run includes RGBA PNGs, optional grayscale alpha PNGs, an optional encoded video, and a settings/source manifest.

Preview frame N replays frames 0 through N using the same processing session as export. This preserves first-frame guidance and temporal state. Seeking deep into a long clip therefore takes processing time; the UI remains responsive and supports cancellation.

Still-image alpha is retained as an upper bound on the newly computed matte. RGB output and processing remain 8-bit, matching the algorithm input contract; 16-bit integer stills are converted to 8-bit. Existing video alpha is not read by the OpenCV path. Video export follows the source's reported constant frame rate and omits audio, as the original overlay exporters did. It does not preserve variable-frame-rate timestamps or HDR metadata. WebM/MP4 pad odd dimensions to the next even dimension. ProRes/WebM carry alpha; green-screen MP4 uses compositing instead.

FFmpeg is an external executable resolved from PATH. PNG exports work without it. Encoder errors include FFmpeg's diagnostic output; completed encoded runs retain `ffmpeg.log`. GUI errors are recorded under `%LOCALAPPDATA%\AlphaFix\logs\alpha-fix.log`.

## Verification

- `uv run pytest -q`: 47 tests and 2 subtests pass, including the retained numerical regressions, bounded jurisdiction and preset guards, project validation/round trips, repeated long/short exports, per-file settings, Unicode paths, existing still alpha, cancellation cleanup, actual video encoding/alpha decoding, and the Qt interaction workflow.
- `uv run python tools/verify_parity.py "E:\Temp\Projects\Tools\Alpha Fix"`: 22 scenarios × 4 frames × 5 arrays = 440 array comparisons, with maximum difference **0.0**. Both engines are exercised with and without guidance in isolated processes, using the same runtime and OpenCV random seed. Report: `parity-report.json`.
- `uv run python -m compileall -q src` and `uv run alpha-fix --help` pass.
- `uv run python tools/render_workspace.py` generates the included demo and renders empty/loaded workspaces for visual inspection.
- Actual ProRes 4444, VP9 WebM alpha and chroma MP4 files were encoded and probed. ProRes/WebM were decoded through alpha extraction to check opaque and transparent regions.

These checks establish numerical parity on representative synthetic inputs and exercise the application workflow. They do not claim new matte quality, new algorithm capability, or acceptance of the private real-artwork benchmark. Original algorithm limitations are preserved, including the operator overlay's outer-edge cleanup policy. Unfinished research probes, old generated exports, private benchmark art, old environments, and coordination history were not copied into the new application.

Implementation references: [Qt thread signals](https://doc.qt.io/qtforpython-6/examples/example_widgets_thread_signals.html), [FFmpeg image sequence format](https://ffmpeg.org/ffmpeg-formats.html#image2-1).
